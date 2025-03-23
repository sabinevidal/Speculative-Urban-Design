import os
import base64
import requests
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Get API key from environment variable
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
STABILITY_API_BASE_URL = "https://api.stability.ai/v2beta"


def verify_stability_api_key():
    """Verify that the Stability AI API key is valid."""
    if not STABILITY_API_KEY:
        raise ValueError(
            "STABILITY_API_KEY not found in environment variables. Make sure to set it in the .env file."
        )

    # A simple check to see if the key is properly formatted (most Stability AI keys start with sk-)
    if not STABILITY_API_KEY.startswith("sk-"):
        print(
            "Warning: Your Stability AI API key doesn't seem to have the expected format."
        )

    return STABILITY_API_KEY


def image_to_base64(image_path):
    """Convert an image file to base64-encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def transform_image_with_prompt(image_path, prompt, strength=0.5, model="sd3.5-medium"):
    """
    Transform an image using the Stability AI API with a text prompt.

    Args:
        image_path: Path to the input image
        prompt: Text prompt to guide the transformation
        strength: How much to transform the image (0.0 to 1.0)
        model: Model to use (default: sd3)

    Returns:
        Response object containing the binary image data
    """
    # Verify API key
    api_key = verify_stability_api_key()

    # Prepare API URL
    api_url = f"{STABILITY_API_BASE_URL}/stable-image/generate/sd3"

    # Prepare the files for the multipart/form-data request
    files = {"image": open(image_path, "rb")}

    # Prepare the form data
    data = {
        "mode": "image-to-image",
        "prompt": prompt,
        "strength": strength,  # How much to transform the image (0.0 to 1.0)
        "model": model,
        "cfg_scale": 5,  # This controls how much the model follows the prompt
        "seed": 0,  # Random seed (0 means random)
    }

    # Set up headers
    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "image/*",
    }

    # Make the API request
    response = requests.post(api_url, headers=headers, files=files, data=data)

    # Check for errors
    if response.status_code != 200:
        try:
            error_json = response.json()
            error_detail = error_json.get("error", {}).get("message", "Unknown error")
        except:
            error_detail = f"Status code: {response.status_code}"
        raise Exception(f"API request failed: {error_detail}")

    return response


def save_generated_images(response, output_dir, base_filename="transformed"):
    """
    Save image from the API response to disk.

    Args:
        response: The API response object with binary image data
        output_dir: Directory to save the image
        base_filename: Base name for the output file

    Returns:
        list: Path to the saved image
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Add timestamp to ensure unique filenames
    timestamp = int(time.time())

    # Save the image
    image_path = os.path.join(output_dir, f"{base_filename}_{timestamp}.png")
    with open(image_path, "wb") as file:
        file.write(response.content)

    return [image_path]
