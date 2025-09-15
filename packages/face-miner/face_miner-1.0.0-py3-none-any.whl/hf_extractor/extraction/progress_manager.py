# hf_extractor/extraction/progress_manager.py
# This file manages the state of the extraction process.
# It centralizes global variables and functions for saving/loading progress.

import threading
import json
import os
from ..config import Config

# --- Global State Management ---

# --- Initialize as an empty dictionary instead of None ---
# This allows the object to be modified in-place from other modules,
# ensuring all parts of the app share the same state.
extraction_result = {}

# A thread-safe lock to prevent race conditions when accessing shared state
extraction_lock = threading.Lock()

# A dictionary to track the real-time progress of the extraction
extraction_progress = {
    "processed": 0,
    "total": 0,
    "start_time": None,
    "status": "idle", # Can be 'idle', 'running', 'complete', 'error'
    "error_message": ""
}

# --- Progress File Handling ---

def save_processed_models(processed_ids_set):
    """
    Saves the set of processed model IDs to a JSON file atomically.
    Uses a temporary file and `os.replace` to prevent data corruption.
    """
    temp_file = Config.PROCESSED_MODELS_FILE + '.tmp'
    try:
        with open(temp_file, 'w') as f:
            json.dump(list(processed_ids_set), f)
        # Atomic operation on most OSes
        os.replace(temp_file, Config.PROCESSED_MODELS_FILE)
        print(f"Progress saved to {Config.PROCESSED_MODELS_FILE}. Total processed: {len(processed_ids_set)}")
    except IOError as e:
        print(f"Error saving progress file: {e}")

def load_processed_models():
    """
    Loads the set of processed model IDs from the JSON progress file.
    Returns an empty set if the file doesn't exist or is corrupt.
    """
    if os.path.exists(Config.PROCESSED_MODELS_FILE):
        try:
            with open(Config.PROCESSED_MODELS_FILE, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading progress file, starting fresh: {e}")
            return set()
    return set()

def reset_progress_file():
    """
    Removes the progress.json file to start a fresh crawl.
    """
    if os.path.exists(Config.PROCESSED_MODELS_FILE):
        try:
            os.remove(Config.PROCESSED_MODELS_FILE)
            print(f"Removed {Config.PROCESSED_MODELS_FILE}")
        except OSError as e:
            print(f"Error removing {Config.PROCESSED_MODELS_FILE}: {e}")
