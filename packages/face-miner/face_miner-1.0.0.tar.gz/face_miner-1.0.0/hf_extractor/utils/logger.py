# hf_extractor/utils/logger.py
# This file sets up a centralized, industry-standard logging configuration.

import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Configures and returns a logger with console and rotating file handlers.
    
    This setup provides two levels of logging:
    - INFO and above messages are printed to the console for real-time monitoring.
    - DEBUG and above messages are written to `app.log` for detailed analysis.
    """
    # Get the root logger for the application
    logger = logging.getLogger("hf_extractor")
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Prevent adding duplicate handlers if this function is called multiple times
    if not logger.handlers:
        # --- Console Handler  ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # Only show INFO, WARNING, ERROR, CRITICAL
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # --- Rotating File Handler  ---
        # Creates a new log file when the current one reaches 5MB, keeping 3 old files.
        file_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3)
        file_handler.setLevel(logging.DEBUG) # Log everything to the file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    return logger

# Create a single logger instance to be imported by other modules
log = setup_logger()
