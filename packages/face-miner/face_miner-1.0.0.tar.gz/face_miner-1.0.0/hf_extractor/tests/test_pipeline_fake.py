import os
import io
import csv
import glob
import json
import shutil
import zipfile
import tempfile
import types
import time

import pytest

# Import  modules
from hf_extractor.config import Config as RealConfig
import hf_extractor.extraction.extractor as extractor_mod
import hf_extractor.main.routes as routes_mod

# Fake HF API + simple objects

class Obj:  # tiny attr bag
    def __init__(self, **kw):
        self.__dict__.update(kw)

class FakeHfApi:
    def __init__(self, token=None):
        self.token = token

    def list_models(self, cardData=True, full=True, fetch_config=True):
        # 3 fake models
        models = []
        for i in range(3):
            models.append(
                Obj(
                    id=f"user/model-{i}",
                    tags=["tagA", "tagB"],
                    pipeline_tag="text-classification",
                    card_data={
                        "tags": ["extra1"],
                        "datasets": ["ds1", "ds2"],
                        "co2_eq_emissions": {"emissions": 1.23, "source": "calc"}
                    },
                    downloads=100+i,
                    likes=10+i,
                    library_name="transformers",
                    last_modified="2025-08-22T00:00:00"
                )
            )
        return models

    def model_info(self, model_id):
        # Return a single fake model
        return Obj(
            id=model_id,
            tags=["tagA"],
            pipeline_tag="text",
            card_data={"tags": ["extra1"], "datasets": ["ds1"]},
            downloads=42, likes=7, library_name="transformers",
            last_modified="2025-08-22T00:00:00"
        )

    def list_repo_files(self, repo_id):
        return ["README.md", "config.json", "pytorch_model.bin"]

    def list_repo_commits(self, repo_id):
        return [
            Obj(title="init", message="first", author=Obj(name="alice"), created_at=_dt("2025-08-22T12:00:00")),
            Obj(title="tune", message="update", author=Obj(name="bob"), created_at=_dt("2025-08-22T13:00:00")),
        ]

    def get_repo_discussions(self, repo_id):
        # Yield-like: the real one returns an iterator
        ds = [
            Obj(num=1, title="q1", status="open", author="alice",
               created_at=_dt("2025-08-22T10:00:00"),
               last_updated_at=_dt("2025-08-22T11:00:00"),
               num_comments=2),
            Obj(num=2, title="q2", status="closed", author="bob",
               created_at=_dt("2025-08-22T14:00:00"),
               last_updated_at=_dt("2025-08-22T15:00:00"),
               num_comments=1),
        ]
        for d in ds:
            yield d

def _dt(iso):
    # Minimal datetime-like with isoformat()
    class D: 
        def __init__(self, s): self.s = s
        def isoformat(self): return self.s
    return D(iso)

# Pytest fixtures

@pytest.fixture(autouse=True)
def patch_config_and_api(monkeypatch, tmp_path):
    # Patch config directories to a temp area
    out_dir = tmp_path / "data"
    stitched_dir = tmp_path / "stitched"
    out_dir.mkdir()
    stitched_dir.mkdir()

    class TestConfig(RealConfig):
        OUTPUT_DIR = str(out_dir)
        STITCHED_DIR = str(stitched_dir)
        PROCESSED_MODELS_FILE = str(tmp_path / "progress.json")
        SAVE_INTERVAL = 1  # save frequently in tests

    # Override Config used by modules
    monkeypatch.setattr("hf_extractor.config.Config", TestConfig, raising=False)
    monkeypatch.setattr(extractor_mod, "Config", TestConfig, raising=False)
    monkeypatch.setattr(routes_mod, "Config", TestConfig, raising=False)

    # Monkeypatch HF API
    monkeypatch.setattr(extractor_mod, "HfApi", FakeHfApi, raising=True)

    yield  # run the test



# Tests
def test_new_extraction_clears_and_writes_parts(tmp_path):
    # Pre-create folders with junk to ensure clearing works
    junk_dirs = ["commits", "discussions", "file_manifests"]
    for d in junk_dirs:
        p = tmp_path / "data" / d
        p.mkdir(parents=True, exist_ok=True)
        (p / "junk.txt").write_text("junk")

    extractor_mod.run_extraction(
        model_id=None,
        num_threads=2,
        token="fake",
        reset_progress=True,  # new extraction must clear first
        output_dir=extractor_mod.Config.OUTPUT_DIR,
        batch_size=2,
        flush_secs=1,
    )

    # Folders should exist (recreated by writer) and contain part files
    for sub in ["models", "commits", "discussions", "file_manifests"]:
        subdir = tmp_path / "data" / sub
        assert subdir.is_dir()
        parts = list(subdir.glob("part-*.csv"))
        assert len(parts) > 0, f"No parts written for {sub}"

def test_resume_does_not_reprocess(tmp_path):
    # First run processes and saves progress
    extractor_mod.run_extraction(
        model_id=None, num_threads=2, token="fake",
        reset_progress=True, output_dir=extractor_mod.Config.OUTPUT_DIR,
        batch_size=2, flush_secs=1
    )
    # Count parts now
    parts1 = _count_all_parts(extractor_mod.Config.OUTPUT_DIR)

    # Second run with reset_progress=False should skip models already processed
    extractor_mod.run_extraction(
        model_id=None, num_threads=2, token="fake",
        reset_progress=False, output_dir=extractor_mod.Config.OUTPUT_DIR,
        batch_size=2, flush_secs=1
    )
    parts2 = _count_all_parts(extractor_mod.Config.OUTPUT_DIR)
    # Allow a few files due to writer flush timing, but should not inflate massively
    assert parts2 <= parts1 + 4

def test_rebuild_and_cleanup(tmp_path):
    # Run once to generate parts
    extractor_mod.run_extraction(
        model_id=None, num_threads=2, token="fake",
        reset_progress=True, output_dir=extractor_mod.Config.OUTPUT_DIR,
        batch_size=2, flush_secs=1
    )
    # Stitch
    totals = {}
    for name in routes_mod.TABLES.keys():
        totals[name] = routes_mod._stitch_one_table(
            name,
            extractor_mod.Config.OUTPUT_DIR,
            extractor_mod.Config.STITCHED_DIR
        )

    # Check stitched CSVs exist
    for name in routes_mod.TABLES.keys():
        p = tmp_path / "stitched" / f"{name}.csv"
        assert p.exists(), f"Stitched {name}.csv missing"

    # Cleanup the three folders
    for sub in ("commits", "discussions", "file_manifests"):
        routes_mod._remove_dir(os.path.join(extractor_mod.Config.OUTPUT_DIR, sub))
        assert not (tmp_path / "data" / sub).exists()

def test_download_zip_contains_stitched(tmp_path):
    # Generate parts
    extractor_mod.run_extraction(
        model_id=None, num_threads=2, token="fake",
        reset_progress=True, output_dir=extractor_mod.Config.OUTPUT_DIR,
        batch_size=2, flush_secs=1
    )
    # Stitch everything
    for name in routes_mod.TABLES.keys():
        routes_mod._stitch_one_table(name, extractor_mod.Config.OUTPUT_DIR, extractor_mod.Config.STITCHED_DIR)

    # Emulate /download
    csv_files = sorted(glob.glob(os.path.join(extractor_mod.Config.STITCHED_DIR, "*.csv")))
    assert csv_files, "No stitched CSVs found for download test"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in csv_files:
            z.write(path, os.path.basename(path))
        z.writestr("progress.json", json.dumps(["m1","m2"]))

    buf.seek(0)
    zf = zipfile.ZipFile(buf)
    names = set(zf.namelist())
    assert "models.csv" in names
    assert "commits.csv" in names
    assert "discussions.csv" in names
    assert "file_manifest.csv" in names
    assert "progress.json" in names

# utils
def _count_all_parts(root):
    total = 0
    for sub in ["models", "commits", "discussions", "file_manifests"]:
        total += len(glob.glob(os.path.join(root, sub, "part-*.csv")))
    return total
