#!/usr/bin/env python3
"""
Utility functions for handling metadata in the urban_future directory.
"""

import os
import json

# Directory constant
RESULTS_DIR = "results/urban_future"


def save_metadata(metadata):
    """
    Save metadata to the urban_future metadata file.

    Args:
        metadata (list): The metadata to save
    """
    # Create directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Save metadata
    metadata_path = os.path.join(RESULTS_DIR, "urban_future_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"Metadata saved to {metadata_path}")


def load_metadata():
    """
    Load metadata from the urban_future metadata file.

    Returns:
        list: List containing urban future metadata
    """
    # Create directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Load metadata
    metadata_path = os.path.join(RESULTS_DIR, "urban_future_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                content = f.read().strip()
                if content:  # File exists and is not empty
                    return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading metadata file: {e}")

    return []
