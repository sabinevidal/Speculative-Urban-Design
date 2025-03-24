import os
import json
import time
from google_maps_api import find_random_urban_street_view, get_street_view_image
from stability_api import transform_image_with_prompt, save_generated_images
import shutil

# Output directories
STREETVIEW_DIR = "streetview_images"
RESULTS_DIR = "results/urban_future"
PROMPT_FILE = "results/prompt_results/cluster_prompts.json"


def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(STREETVIEW_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Ensure the metadata JSON file exists and is properly initialized
    metadata_path = os.path.join(RESULTS_DIR, "urban_future_metadata.json")
    if not os.path.exists(metadata_path):
        with open(metadata_path, "w") as f:
            f.write("[]")


def load_cluster_prompts():
    """
    Load cluster prompts from the JSON file.

    Returns:
        dict: Dictionary containing cluster prompts or an empty dict if file not found
    """
    try:
        with open(PROMPT_FILE, "r") as f:
            prompts = json.load(f)
        return prompts
    except Exception as e:
        print(f"Error loading cluster prompts: {e}")
        return {}


def get_available_prompt_ids():
    """
    Get a list of available prompt IDs for the dropdown.

    Returns:
        list: List of prompt IDs
    """
    prompts = load_cluster_prompts()
    return list(prompts.keys())


def get_available_prompt_names():
    """
    Get a list of available prompt names for the dropdown.

    Returns:
        list: List of prompt names
    """
    prompts = load_cluster_prompts()
    return [prompts[id]["name"] for id in prompts]


def get_prompt_by_name(prompt_name):
    """
    Get a specific prompt by its name.

    Args:
        prompt_name: The name of the prompt (cluster ID)

    Returns:
        str: The prompt text or a default prompt if not found
    """
    prompts = load_cluster_prompts()

    if prompt_name in prompts:
        return prompts[prompt_name]["prompt"]

    # Return a default prompt if the requested one is not found
    return "Transform this urban street into a sustainable city design with modern architecture, green spaces, and improved infrastructure"


def transform_street_view(image_path, prompt, strength=0.7, prompt_name=None):
    """
    Transform a street view image into a speculative urban future image.

    Args:
        image_path (str): Path to the street view image
        prompt (str): Prompt for the transformation
        strength (float): Strength of the transformation (0.0-1.0)
        prompt_name (str, optional): Name of the prompt for metadata

    Returns:
        dict: Dictionary containing the transformation results
    """
    try:
        # Call Stability AI API to transform the image
        response = transform_image_with_prompt(
            image_path=image_path,
            prompt=prompt,
            strength=strength,
            model="sd3.5-medium",  # Using Stable Diffusion 3.5 for higher quality
        )

        # Save the generated images
        image_basename = os.path.basename(image_path).split(".")[0]
        output_dir = os.path.join(RESULTS_DIR, image_basename)
        saved_images = save_generated_images(
            response, output_dir, f"urban_future_{image_basename}"
        )

        # Create result dictionary
        result = {
            "success": True,
            "original_image": image_path,
            "transformed_images": saved_images,
            "prompt": prompt,
            "prompt_name": prompt_name,
        }

        # Save metadata when transform_street_view is called directly
        # Load existing metadata
        metadata = load_metadata()

        # Add the new result to metadata
        metadata.append(
            {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "heading": 0,
                "original_image": result["original_image"],
                "transformed_images": result["transformed_images"],
                "prompt": result["prompt"],
                "prompt_name": prompt_name,
            }
        )

        # Save the updated metadata
        save_metadata(metadata)

        return result

    except Exception as e:
        print(f"Error in transform_street_view: {e}")
        return {"success": False, "original_image": image_path, "error": str(e)}


def load_metadata():
    """
    Load the urban future metadata from the JSON file.

    Returns:
        list: List containing urban future metadata
    """
    metadata_path = os.path.join(RESULTS_DIR, "urban_future_metadata.json")

    # Ensure the file exists
    if not os.path.exists(metadata_path):
        with open(metadata_path, "w") as f:
            f.write("[]")
        return []

    # Load the metadata
    try:
        with open(metadata_path, "r") as f:
            content = f.read().strip()
            if not content:  # File exists but is empty
                return []
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading metadata file: {e}")
        # Reset the file if it's corrupted
        with open(metadata_path, "w") as f:
            f.write("[]")
        return []


def save_metadata(metadata):
    """
    Save the urban future metadata to the JSON file.

    Args:
        metadata (list): List containing urban future metadata
    """
    metadata_path = os.path.join(RESULTS_DIR, "urban_future_metadata.json")

    # Ensure we're not overwriting existing data
    existing_metadata = []
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                content = f.read().strip()
                if content:  # File exists and is not empty
                    existing_metadata = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, we'll start with an empty list
            existing_metadata = []

    # If metadata is a single entry, convert it to a list
    if isinstance(metadata, dict):
        metadata = [metadata]

    # Combine existing metadata with new metadata
    combined_metadata = existing_metadata + metadata

    # Write the combined metadata back to the file
    with open(metadata_path, "w") as f:
        json.dump(combined_metadata, f, indent=4)
