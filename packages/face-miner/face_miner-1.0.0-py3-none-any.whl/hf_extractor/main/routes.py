# hf_extractor/main/routes.py
# Web routes (Flask)

import os
import io
import csv
import glob
import json
import time
import shutil
import zipfile
import threading
from typing import List, Dict, Tuple, Set

from flask import render_template, request, jsonify, send_file

from . import main_bp
from ..config import Config
from ..extraction.extractor import run_extraction
from ..extraction.progress_manager import extraction_progress, extraction_result, extraction_lock, load_processed_models
from ..utils import schema_generator

# Helpers for stitching

TABLES = {
    "models": {"dir": "models", "pk": ["modelId"]},
    "commits": {"dir": "commits", "pk": ["modelId", "commit_created_at", "commit_title", "commit_author"]},
    "discussions": {"dir": "discussions", "pk": ["modelId", "discussion_id"]},
    "file_manifest": {"dir": "file_manifests", "pk": ["modelId", "file_path"]},
}

def _list_parts(table_dir: str) -> List[str]:
    return sorted(
        f for f in glob.glob(os.path.join(table_dir, "part-*.csv"))
        if not f.endswith(".tmp")
    )

def _union_headers(files: List[str]) -> List[str]:
    seen, order = set(), []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", newline="") as fh:
                reader = csv.reader(fh)
                header = next(reader, None)
                if not header: 
                    continue
                for col in header:
                    if col not in seen:
                        seen.add(col)
                        order.append(col)
        except Exception:
            # skip bad header file
            pass
    return order

def _stitch_one_table(name: str, root_dir: str, out_dir: str) -> int:
    table_dir = os.path.join(root_dir, TABLES[name]["dir"])
    parts = _list_parts(table_dir)
    if not parts:
        return 0

    headers = _union_headers(parts)
    if not headers:
        return 0

    pk = TABLES[name]["pk"]
    seen: Set[Tuple[str, ...]] = set()

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}.csv")
    tmp = out_path + ".tmp"
    count = 0

    with open(tmp, "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        for path in parts:
            try:
                with open(path, "r", encoding="utf-8", newline="") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        key = tuple((row.get(c, "") or "") for c in pk)
                        if key in seen:
                            continue
                        seen.add(key)
                        safe = {c: row.get(c, "") for c in headers}
                        writer.writerow(safe)
                        count += 1
            except Exception:
                # skip unreadable part; keep going
                continue

        try:
            out.flush()
            os.fsync(out.fileno())
        except Exception:
            pass

    os.replace(tmp, out_path)
    return count

def _remove_dir(path: str):
    if os.path.isdir(path):
        shutil.rmtree(path)

# Routes

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/extract', methods=['POST'])
def extract():
    with extraction_lock:
        if extraction_progress["status"] == "running":
            return jsonify({"error": "An extraction process is already running."}), 409

    data = request.json or {}
    model_id = data.get('model_id')
    num_threads = data.get('num_threads', 8)
    token = data.get('token')
    reset_progress = data.get('reset_progress', True)

    # Start background extraction; write parts under Config.OUTPUT_DIR
    threading.Thread(
        target=run_extraction,
        args=(model_id, num_threads, token, reset_progress, Config.OUTPUT_DIR),
        daemon=True
    ).start()

    return jsonify({"message": "Extraction process started!"})

@main_bp.route('/status')
def status():
    with extraction_lock:
        progress = extraction_progress.copy()

    if progress["status"] == "running" and progress["processed"] > 0 and progress.get("total", 0) > 0:
        elapsed = time.time() - progress["start_time"]
        if progress["processed"] > 0:
            per_item = max(elapsed / progress["processed"], 1e-6)
            remain = (progress["total"] - progress["processed"]) * per_item
            progress["estimated_time_remaining"] = round(remain)
        else:
            progress["estimated_time_remaining"] = "Calculating..."
    else:
        progress["estimated_time_remaining"] = "N/A"

    return jsonify(progress)

@main_bp.route('/rebuild_and_cleanup', methods=['POST'])
def rebuild_and_cleanup():
    """
    Stitch all part CSVs into stitched/*.csv and then delete
    commits/, discussions/, file_manifests/ under OUTPUT_DIR.
    """
    root = Config.OUTPUT_DIR
    out_dir = Config.STITCHED_DIR
    os.makedirs(out_dir, exist_ok=True)

    totals: Dict[str, int] = {}
    for name in TABLES.keys():
        totals[name] = _stitch_one_table(name, root, out_dir)

    # Remove the three big folders after stitching
    _remove_dir(os.path.join(root, "commits"))
    _remove_dir(os.path.join(root, "discussions"))
    _remove_dir(os.path.join(root, "file_manifests"))

    return jsonify({
        "ok": True,
        "stitched_dir": out_dir,
        "rows_written": totals
    })

@main_bp.route('/download')
def download():
    """
    Zip and download the stitched CSVs from STITCHED_DIR.
    """
    stitched_dir = Config.STITCHED_DIR
    # find CSVs
    csv_files = sorted(glob.glob(os.path.join(stitched_dir, "*.csv")))
    if not csv_files:
        return "No stitched CSVs found. Run extraction and rebuilding first.", 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in csv_files:
            arcname = os.path.basename(path)
            z.write(path, arcname)
        processed = json.dumps(list(load_processed_models()), indent=2)
        z.writestr('progress.json', processed)
        try:
            # Build a fake extraction_result-like dict of DataFrames just for schema
            import pandas as pd
            ers = {}
            for path in csv_files:
                name = os.path.splitext(os.path.basename(path))[0]
                ers[name] = pd.read_csv(path)
            schema_md = schema_generator.describe_csv_columns(ers)
            z.writestr('schema.md', schema_md)
        except Exception:
            pass

    buf.seek(0)
    return send_file(buf, mimetype='application/zip', as_attachment=True, download_name='huggingface_data.zip')
