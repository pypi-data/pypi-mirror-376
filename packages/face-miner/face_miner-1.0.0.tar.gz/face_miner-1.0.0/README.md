# Hugging Face Extractor

A web-based tool to extract metadata for models from the Hugging Face Hub.

## Features

* Extract information for a single model or all models.
* Fetches metadata, tags, datasets, CO2 emissions, commits, discussions, and file manifests.
* Multi-threaded extraction for performance.
* Download the extracted data as a ZIP file containing multiple CSVs.
* Ability to resume a full crawl if interrupted.

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/hf-extractor.git](https://github.com/yourusername/hf-extractor.git)
    cd hf-extractor
    ```

2.  Install the required packages and make the project recognizable as a local package:
    ```bash
    pip install -e .
    ```

## Usage

1.  Run the Flask application from the project's root directory:
    ```bash
    python run.py
    ```

2.  Open your web browser and navigate to `http://127.0.0.1:5050`.

3.  Use the web interface to start the extraction process.