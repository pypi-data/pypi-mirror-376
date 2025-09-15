# hf_extractor/extraction/extractor.py
# Core business logic for fetching and processing model data.
# REFACTORED FOR SCALABILITY, MEMORY EFFICIENCY, AND CSV-ONLY OUTPUT

import os
import time
import json
import uuid
import random
import shutil
import pandas as pd
import itertools
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from huggingface_hub.hf_api import HfApi
from huggingface_hub.utils import HfHubHTTPError

from .progress_manager import (
    extraction_progress,
    extraction_result,
    extraction_lock,
    save_processed_models,
    load_processed_models,
    reset_progress_file
)
from ..config import Config
from ..utils.logger import log

# ------------------------------
# Helper Functions
# ------------------------------

def retrieve_emission_parameters(model):
    """Safely extracts CO2 emission data from a model's card data."""
    if not hasattr(model, 'card_data') or not model.card_data or 'co2_eq_emissions' not in model.card_data:
        return None, None, None, None, None
    co2_data = model.card_data.get("co2_eq_emissions", {})
    if isinstance(co2_data, dict):
        emissions = co2_data.get("emissions")
        source = co2_data.get('source')
        training_type = co2_data.get('training_type')
        geographical_location = co2_data.get('geographical_location')
        hardware_used = co2_data.get('hardware_used')
        return emissions, source, training_type, geographical_location, hardware_used
    return co2_data, None, None, None, None

def retrieve_model_tags(model):
    """Consolidates tags from various fields in the model object."""
    tags = set(model.tags or [])
    if getattr(model, 'pipeline_tag', None):
        tags.add(model.pipeline_tag)
    if hasattr(model, 'card_data') and model.card_data and 'tags' in model.card_data:
        card_tags = model.card_data['tags']
        if isinstance(card_tags, list):
            try:
                tags.update(card_tags)
            except TypeError:
                pass
        else:
            tags.add(card_tags)
    return [tag for tag in tags if tag is not None]

def retrieve_model_datasets(model):
    """Safely extracts dataset information from a model's card data."""
    if hasattr(model, 'card_data') and model.card_data and 'datasets' in model.card_data:
        datasets = model.card_data.get("datasets")
        return datasets if isinstance(datasets, list) else [datasets]
    return []  # ensure a list

# ------------------------------
# CSV Data Writer (Producer/Consumer)
# ------------------------------

class DataWriter(threading.Thread):
    """
    Single consumer thread that drains a queue and writes CSV 'part' files atomically.
    - Writes per-type batches to: <output_dir>/<type>s/part-<ts>-<uuid>.csv
    - Size-based and time-based flush to bound in-memory data if a crash occurs.
    - Uses temp file + os.replace for atomicity.
    """
    def __init__(self, writer_queue, output_dir, batch_size=1000, flush_secs=10):
        super().__init__()
        self.writer_queue = writer_queue
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.flush_secs = flush_secs

        self.batches = {
            'model': [],
            'commit': [],
            'discussion': [],
            'file_manifest': []
        }
        self.shutdown_signals_expected = len(self.batches)
        self.shutdown_signals_received = 0
        self.last_flush = time.time()

        # Prepare directories
        for sub in self.batches.keys():
            os.makedirs(os.path.join(self.output_dir, f"{sub}s"), exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, f"{sub}s", "tmp"), exist_ok=True)

    def _write_batch_part_csv(self, data_type):
        rows = self.batches[data_type]
        if not rows:
            return

        df = pd.DataFrame(rows)
        ts = time.strftime("%Y%m%d-%H%M%S")
        part_name = f"part-{ts}-{uuid.uuid4().hex[:8]}.csv"

        final_dir = os.path.join(self.output_dir, f"{data_type}s")
        tmp_dir = os.path.join(final_dir, "tmp")
        final_path = os.path.join(final_dir, part_name)
        tmp_path = os.path.join(tmp_dir, part_name + ".tmp")

        try:
            df.to_csv(tmp_path, index=False)
            try:
                with open(tmp_path, "rb") as f:
                    os.fsync(f.fileno())
            except Exception:
                pass
            os.replace(tmp_path, final_path)
            log.debug(f"Wrote {len(rows)} '{data_type}' rows to {final_path}")
        except Exception as e:
            log.error(f"Error writing CSV batch for '{data_type}': {e}", exc_info=True)
        finally:
            self.batches[data_type].clear()

    def _maybe_flush(self, force=False):
        now = time.time()
        if force or (now - self.last_flush >= self.flush_secs):
            for t in self.batches.keys():
                if len(self.batches[t]) > 0:
                    self._write_batch_part_csv(t)
            self.last_flush = now

    def run(self):
        log.info("DataWriter thread started.")
        pulls = 0
        while self.shutdown_signals_received < self.shutdown_signals_expected:
            try:
                msg = self.writer_queue.get(timeout=1)
                if msg is None:
                    self.shutdown_signals_received += 1
                    continue

                msg_type = msg['type']
                data = msg['data']
                if msg_type not in self.batches:
                    log.warning(f"Unknown message type: {msg_type}; skipping")
                    continue

                self.batches[msg_type].append(data)
                pulls += 1

                if len(self.batches[msg_type]) >= self.batch_size:
                    self._write_batch_part_csv(msg_type)

                if pulls % 200 == 0:
                    self._maybe_flush(False)

            except queue.Empty:
                self._maybe_flush(False)
                continue
            except Exception as e:
                log.critical(f"Critical error in DataWriter thread: {e}", exc_info=True)

        log.info("Writer shutdown signaled. Flushing remaining batches...")
        self._maybe_flush(True)
        log.info("DataWriter finished. All CSV parts are written.")

# ------------------------------
# Local helpers
# ------------------------------

def _remove_dir(path: str):
    """Delete a directory tree if it exists (quietly)."""
    if os.path.isdir(path):
        shutil.rmtree(path)

# ------------------------------
# Main Processing
# ------------------------------

def process_model(model, api_client, extraction_timestamp, writer_queue):
    """
    Processes a single model and puts the extracted data onto the writer queue.
    Returns model.id for progress tracking on success, else None.
    """
    try:
        tags = retrieve_model_tags(model)
        datasets = retrieve_model_datasets(model)
        emissions, source, training_type, geo, hardware = retrieve_emission_parameters(model)

        # Files
        for attempt in range(5):
            try:
                repo_files = api_client.list_repo_files(repo_id=model.id)
                for file_path in sorted(list(repo_files)):
                    writer_queue.put({
                        'type': 'file_manifest',
                        'data': {
                            'modelId': model.id,
                            'file_path': file_path,
                            'extraction_timestamp': extraction_timestamp
                        }
                    })
                break
            except (HfHubHTTPError, Exception) as e:
                if attempt == 4:
                    log.warning(f"File manifest fetch failed for {model.id}: {e}")
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

        # Commits
        for attempt in range(5):
            try:
                commits = api_client.list_repo_commits(repo_id=model.id)
                for commit in commits:
                    commit_created_at = getattr(commit, 'created_at', None)
                    writer_queue.put({
                        'type': 'commit',
                        'data': {
                            'modelId': model.id,
                            'commit_title': getattr(commit, 'title', 'N/A'),
                            'commit_message': getattr(commit, 'message', 'N/A'),
                            'commit_author': getattr(getattr(commit, 'author', None), 'name', 'N/A'),
                            'commit_created_at': commit_created_at.isoformat() if commit_created_at else 'N/A',
                            'extraction_timestamp': extraction_timestamp
                        }
                    })
                break
            except Exception as e:
                if "gated" in str(e).lower():
                    log.debug(f"Skipping commits for gated repo {model.id}")
                    break
            except Exception as e:
                if attempt == 4:
                    log.warning(f"Commit fetch failed for {model.id}: {e}")
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

        # Discussions
        discussions_count = 0
        for attempt in range(5):
            try:
                discussions = list(api_client.get_repo_discussions(repo_id=model.id))
                discussions_count = len(discussions)
                for d in discussions:
                    writer_queue.put({
                        'type': 'discussion',
                        'data': {
                            'modelId': model.id,
                            'discussion_id': getattr(d, 'num', 'N/A'),
                            'title': getattr(d, 'title', 'N/A'),
                            'status': getattr(d, 'status', 'N/A'),
                            'author': getattr(d, 'author', 'N/A'),
                            'created_at': getattr(d, 'created_at', 'N/A').isoformat() if getattr(d, 'created_at', None) else 'N/A',
                            'last_updated_at': getattr(d, 'last_updated_at', 'N/A').isoformat() if getattr(d, 'last_updated_at', None) else 'N/A',
                            'num_comments': getattr(d, 'num_comments', 0),
                            'extraction_timestamp': extraction_timestamp
                        }
                    })
                break
            except HfHubHTTPError as e:
                if e.response.status_code == 404 or "disabled" in str(e).lower():
                    discussions_count = 0
                    break
                if attempt == 4:
                    log.warning(f"Discussion fetch failed for {model.id}: {e}")
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 1))
            except Exception as e:
                if attempt == 4:
                    log.warning(f"Unexpected error fetching discussions for {model.id}: {e}")
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 1))

        # Model info (1 row)
        writer_queue.put({
            'type': 'model',
            'data': {
                'modelId': model.id,
                'tags': json.dumps(tags),
                'datasets': json.dumps(datasets),
                'co2_eq_emissions': emissions,
                'source': source,
                'training_type': training_type,
                'geographical_location': geo,
                'hardware_used': hardware,
                'downloads': model.downloads,
                'likes': model.likes,
                'library_name': getattr(model, 'library_name', None),
                'lastModified': model.last_modified,
                'extraction_timestamp': extraction_timestamp,
                'discussions_count': discussions_count
            }
        })

        return model.id

    except Exception as e:
        log.error(f"CRITICAL ERROR processing model {getattr(model, 'id', 'Unknown')}: {e}", exc_info=True)
        return None


def run_extraction(
    model_id=None,
    num_threads=8,
    token=None,
    reset_progress=True,
    output_dir=Config.OUTPUT_DIR,
    batch_size=1000,
    flush_secs=10
):
    """
    Orchestrates producers (fetching) and a consumer (CSV writer).
    Produces crash-safe CSV part files per data type.
    """
    extraction_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    api_client = HfApi(token=token)
    CHUNK_SIZE = 100
    QUEUE_MAX_SIZE = num_threads * 2  # backpressure

    if reset_progress:
        dirs_to_clear = ["commits", "discussions", "file_manifests"]
        if Config.CLEAR_MODELS_ON_NEW_EXTRACTION:
            dirs_to_clear.append("models")  

        for sub in dirs_to_clear:
            _remove_dir(os.path.join(output_dir, sub))

        log.info(
            f"Starting a new crawl. Progress file reset and part folders cleared: "
            f"{', '.join(dirs_to_clear)} under {os.path.abspath(output_dir)}"
        )

    # Setup writer thread AFTER cleanup
    writer_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
    data_writer = DataWriter(writer_queue, output_dir, batch_size=batch_size, flush_secs=flush_secs)
    data_writer.start()

    # Initialize progress
    with extraction_lock:
        extraction_progress.update({
            "status": "initializing",
            "start_time": time.time(),
            "processed": 0,
            "total": 0,
            "error_message": "",
            "chunk_number": 0,
            "chunk_processed": 0,
            "chunk_total": 0,
            "extraction_type": "single" if model_id else "full",
        })
        extraction_result.clear()
        if model_id is None and reset_progress:
            reset_progress_file()
            log.info("Starting a new crawl. Progress file reset and part folders cleared.")
        elif model_id is None:
            log.info("Resuming full crawl. Loading previous progress.")

    processed_model_ids = set()
    if model_id is None:
        processed_model_ids = load_processed_models()
        log.info(f"Loaded {len(processed_model_ids)} previously processed models.")
        with extraction_lock:
            extraction_progress["processed"] = len(processed_model_ids)

    try:
        if model_id:
            # Single model
            log.info(f"Fetching single model: {model_id}")
            with extraction_lock:
                extraction_progress.update({"total": 1, "status": "running"})
            try:
                model_obj = api_client.model_info(model_id)
                processed_id = process_model(model_obj, api_client, extraction_timestamp, writer_queue)
                if processed_id:
                    with extraction_lock:
                        extraction_progress["processed"] += 1
            except HfHubHTTPError as e:
                log.error(f"Error fetching single model '{model_id}': {e}")
                with extraction_lock:
                    extraction_progress.update({"status": "error", "error_message": f"Model '{model_id}' not found."})
        else:
            # Full crawl
            log.info("Starting full model crawl...")
            with extraction_lock:
                extraction_progress["status"] = "running"

            model_generator = api_client.list_models(cardData=True, full=True, fetch_config=True)
            models_to_process_generator = (m for m in model_generator if m.id not in processed_model_ids)

            chunk_number = 1
            processed_in_this_run = 0

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                while True:
                    with extraction_lock:
                        extraction_progress["chunk_number"] = chunk_number
                        extraction_progress["chunk_processed"] = 0

                    chunk = list(itertools.islice(models_to_process_generator, CHUNK_SIZE))
                    if not chunk:
                        log.info("No more models to process.")
                        break

                    with extraction_lock:
                        extraction_progress["chunk_total"] = len(chunk)

                    log.info(f"Processing chunk {chunk_number} with {len(chunk)} models.")

                    futures = {
                        executor.submit(process_model, m, api_client, extraction_timestamp, writer_queue): m
                        for m in chunk
                    }
                    for future in as_completed(futures):
                        processed_id = future.result()
                        if processed_id:
                            processed_model_ids.add(processed_id)
                            with extraction_lock:
                                extraction_progress["processed"] += 1
                                extraction_progress["chunk_processed"] += 1

                            processed_in_this_run += 1
                            if processed_in_this_run % Config.SAVE_INTERVAL == 0:
                                save_processed_models(processed_model_ids)

                    chunk_number += 1

        with extraction_lock:
            if model_id is None:
                extraction_progress["total"] = extraction_progress["processed"]
                save_processed_models(processed_model_ids)
            extraction_progress["status"] = "complete"
        log.info("Extraction process completed successfully.")

    except Exception as e:
        with extraction_lock:
            extraction_progress.update({"status": "error", "error_message": str(e)})
        log.critical(f"Extraction process encountered a critical error: {e}", exc_info=True)
    finally:
        log.info("Main process finished. Signaling writer thread to shut down.")
        for _ in range(len(data_writer.batches)):
            writer_queue.put(None)
        data_writer.join()
        log.info("Writer thread has shut down. Application exiting.")
