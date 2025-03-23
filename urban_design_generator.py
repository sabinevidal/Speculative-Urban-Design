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


def generate_urban_design_from_random_location(
    prompt_name=None, strength=0.5, attempts=3
):
    """
    Generate an urban design concept from a random street view.

    This function:
    1. Finds a random urban street view
    2. Uses the specified prompt from cluster prompts
    3. Transforms the image using the Stability AI API
    4. Saves the results

    Args:
        prompt_name: Name of the prompt to use from cluster_prompts.json
        strength: How much to transform the image (0.0 to 1.0)
        attempts: Number of attempts to find a valid street view

    Returns:
        dict: Information about the generated design
    """
    setup_directories()

    # Find a random street view
    street_view_result = find_random_urban_street_view(STREETVIEW_DIR, attempts)

    if not street_view_result["success"]:
        return {"success": False, "error": street_view_result["error"]}

    # Get the prompt from the cluster prompts file
    prompt = (
        get_prompt_by_name(prompt_name)
        if prompt_name
        else get_prompt_by_name(get_available_prompt_names()[0])
    )

    # Transform the street view image
    transform_result = transform_street_view(
        street_view_result["image_path"],
        prompt,
        strength,
        prompt_name,
    )

    if not transform_result["success"]:
        return {
            "success": False,
            "error": transform_result["error"],
            "location": street_view_result["location"],
        }

    # Combine all results for return
    result = {
        "success": True,
        "location": street_view_result["location"],
        "latitude": street_view_result["latitude"],
        "longitude": street_view_result["longitude"],
        "heading": street_view_result["heading"],
        "original_image": transform_result["original_image"],
        "transformed_images": transform_result["transformed_images"],
        "prompt": transform_result["prompt"],
        "prompt_name": prompt_name,
    }

    # Load existing metadata
    metadata = load_metadata()

    # Add the new result
    metadata.append(
        {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": result["location"],
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "heading": result["heading"],
            "original_image": result["original_image"],
            "transformed_images": result["transformed_images"],
            "prompt": result["prompt"],
            "prompt_name": prompt_name,
        }
    )

    # Save the updated metadata
    save_metadata(metadata)

    return result


def generate_designs_for_specific_location(place, prompt_name=None, strength=0.75):
    """
    Generate urban design concepts for a specific location.

    This function:
    1. Gets a street view for the specified place
    2. Uses the specified prompt from cluster prompts
    3. Transforms the image using the Stability AI API

    Args:
        place: String value of a place's name
        prompt_name: Name of the prompt to use from cluster_prompts.json
        strength: How much to transform the images (0.0 to 1.0)

    Returns:
        dict: Information about the generated designs
    """
    setup_directories()

    # Get the prompt from the cluster prompts file
    prompt = (
        get_prompt_by_name(prompt_name)
        if prompt_name
        else get_prompt_by_name(get_available_prompt_names()[0])
    )

    results = []

    # Generate one or multiple views
    street_view = get_street_view_image(place)

    if not street_view["success"]:
        return {"success": False, "error": street_view["error"]}

    # Save the street view image
    image_path = os.path.join(
        STREETVIEW_DIR,
        f"street_view_{street_view['latitude']}_{street_view['longitude']}_{street_view['heading']}.jpg",
    )
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    # Save image
    street_view["image_pil"].save(image_path)
    # Transform image with the selected prompt
    transform_result = transform_street_view(image_path, prompt, strength, prompt_name)
    if transform_result["success"]:
        results.append(
            {
                "location": street_view["address"],
                "latitude": street_view["latitude"],
                "longitude": street_view["longitude"],
                "heading": street_view["heading"],
                "original_image": transform_result["original_image"],
                "transformed_images": transform_result["transformed_images"],
                "prompt": transform_result["prompt"],
                "prompt_name": prompt_name,
            }
        )

    # If we found at least one valid view, consider it a success
    if results:
        # Load existing metadata
        metadata = load_metadata()

        # Add each result to metadata
        for result in results:
            metadata.append(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "location": result["location"],
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "heading": result["heading"],
                    "original_image": result["original_image"],
                    "transformed_images": result["transformed_images"],
                    "prompt": result["prompt"],
                    "prompt_name": result["prompt_name"],
                }
            )

        # Save the updated metadata
        save_metadata(metadata)

        return {
            "success": True,
            "location": street_view["address"],
            "results": results,
        }
    else:
        return {
            "success": False,
            "error": "Could not obtain street views at this location",
        }


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


if __name__ == "__main__":
    # Example usage: Generate a design from a random location
    available_prompts = get_available_prompt_names()
    if available_prompts:
        print(f"Available prompts: {available_prompts}")
        result = generate_urban_design_from_random_location(
            prompt_name=available_prompts[0], strength=0.5
        )
    else:
        print("No prompts found in cluster_prompts.json, using default prompt")
        result = generate_urban_design_from_random_location(strength=0.5)

    if result["success"]:
        print(f"Successfully generated urban design for {result['location']}")
        print(f"Original image: {result['original_image']}")
        print(f"Transformed images: {result['transformed_images']}")
        print(f"Prompt used: {result['prompt']}")
    else:
        print(f"Error: {result['error']}")
