import os
import json
import time
from google_maps_api import find_random_urban_street_view, get_street_view_image
from stability_api import transform_image_with_prompt, save_generated_images
import shutil

# Output directories
STREETVIEW_DIR = "sample_images/street_view"
RESULTS_DIR = "results/urban_design"
PROMPT_FILE = "results/prompt_results/cluster_prompts.json"


def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(STREETVIEW_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Ensure the metadata JSON file exists and is properly initialized
    metadata_path = os.path.join(RESULTS_DIR, "urban_design_metadata.json")
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
    Transform a street view image using Stability AI API.

    Args:
        image_path: Path to the street view image
        prompt: Text prompt for the transformation
        strength: How much to transform the image (0.0 to 1.0)
        prompt_name: The cluster ID/name of the prompt used

    Returns:
        dict: Information about the transformed image(s)
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
            response, output_dir, f"urban_design_{image_basename}"
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
    Load the urban design metadata from the JSON file.

    Returns:
        list: List containing urban design metadata
    """
    metadata_path = os.path.join(RESULTS_DIR, "urban_design_metadata.json")

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
    Save the urban design metadata to the JSON file.

    Args:
        metadata (list): List containing urban design metadata
    """
    metadata_path = os.path.join(RESULTS_DIR, "urban_design_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
