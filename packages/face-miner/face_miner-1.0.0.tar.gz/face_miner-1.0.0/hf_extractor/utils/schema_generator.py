# hf_extractor/utils/schema_generator.py
# This file contains utility functions that are not directly related to
# the core extraction logic or web routes.

def describe_csv_columns(extraction_result):
    """
    Generates a markdown string describing the columns of the output CSV files.
    """
    model_col_desc = {
        "modelId": "The unique identifier of the Hugging Face model.",
        "tags": "A JSON-encoded list of tags associated with the model.",
        "datasets": "A JSON-encoded list of datasets used by the model.",
        "co2_eq_emissions": "Estimated CO2 equivalent emissions for training the model.",
        "source": "Source of the emissions data.",
        "training_type": "Type of training (e.g., pretraining, finetuning).",
        "geographical_location": "Geographical location where the model was trained.",
        "hardware_used": "Hardware used for training.",
        "downloads": "Number of downloads of the model.",
        "likes": "Number of likes on the model.",
        "library_name": "The library/framework used (if available).",
        "lastModified": "Timestamp of the last modification to the model.",
        "extraction_timestamp": "Timestamp when this extraction was performed.",
        "discussions_count": "Number of discussions associated with the model."
    }
    commit_col_desc = {
        "modelId": "The unique identifier of the Hugging Face model.",
        "commit_title": "Title of the commit.",
        "commit_message": "Commit message.",
        "commit_author": "Author of the commit.",
        "commit_created_at": "Timestamp when the commit was created.",
        "extraction_timestamp": "Timestamp when this extraction was performed."
    }
    discussion_col_desc = {
        "modelId": "The unique identifier of the Hugging Face model.",
        "discussion_id": "Unique ID of the discussion.",
        "title": "Title of the discussion.",
        "status": "Status of the discussion (e.g., 'open', 'closed').",
        "author": "Author of the discussion.",
        "created_at": "Timestamp when the discussion was created.",
        "last_updated_at": "Timestamp when the discussion was last updated.",
        "num_comments": "Number of comments in the discussion.",
        "extraction_timestamp": "Timestamp when this extraction was performed.",
    }
    file_manifest_col_desc = {
        "modelId": "The unique identifier of the Hugging Face model.",
        "file_path": "The path of the file within the model repository.",
        "extraction_timestamp": "Timestamp when this extraction was performed."
    }

    lines = ["# CSV Column Descriptions\n"]
    
    # Describe models.csv
    lines.append("## models.csv\n")
    lines.append("| Column | Description |")
    lines.append("|--------|-------------|")
    for col in extraction_result["models"].columns:
        desc = model_col_desc.get(col, "")
        lines.append(f"| `{col}` | {desc} |")
    lines.append("")

    # Describe commits.csv
    lines.append("## commits.csv\n")
    lines.append("| Column | Description |")
    lines.append("|--------|-------------|")
    for col in extraction_result["commits"].columns:
        desc = commit_col_desc.get(col, "")
        lines.append(f"| `{col}` | {desc} |")
    lines.append("")

    # Describe discussions.csv
    if 'discussions' in extraction_result and not extraction_result['discussions'].empty:
        lines.append("## discussions.csv\n")
        lines.append("| Column | Description |")
        lines.append("|--------|-------------|")
        for col in extraction_result["discussions"].columns:
            desc = discussion_col_desc.get(col, "")
            lines.append(f"| `{col}` | {desc} |")
        lines.append("")

    # Describe file_manifest.csv
    if 'file_manifest' in extraction_result and not extraction_result['file_manifest'].empty:
        lines.append("## file_manifest.csv\n")
        lines.append("| Column | Description |")
        lines.append("|--------|-------------|")
        for col in extraction_result["file_manifest"].columns:
            desc = file_manifest_col_desc.get(col, "")
            lines.append(f"| `{col}` | {desc} |")
        lines.append("")

    return "\n".join(lines)