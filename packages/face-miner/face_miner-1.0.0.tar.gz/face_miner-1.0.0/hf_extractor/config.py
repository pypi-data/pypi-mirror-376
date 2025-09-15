# hf_extractor/config.py
# Centralized configuration

import os

class Config:
    """
    Configuration class for the Flask application.
    """
    # Where we persist the list of processed model IDs (atomic JSON)
    PROCESSED_MODELS_FILE = 'progress.json'

    # Save processed IDs every N models
    SAVE_INTERVAL = 50

    # list_models limit if you ever decide to use it
    DEFAULT_LIST_LIMIT = 5000

    # Directory where part CSVs are written:
    OUTPUT_DIR = os.environ.get("HF_EXTRACTOR_OUTPUT_DIR", "data")
    # Directory where stitched/final CSVs are written:
    STITCHED_DIR = os.environ.get("HF_EXTRACTOR_STITCHED_DIR", "stitched")
    CLEAR_MODELS_ON_NEW_EXTRACTION = True
