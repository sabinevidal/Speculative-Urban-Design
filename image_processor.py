#!/usr/bin/env python3
import os
import argparse
import base64
import json
import glob
from io import BytesIO
from datetime import datetime
import time

from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from prompt_handler import get_analysis_prompt, get_openai_input

# Load environment variables from .env file
load_dotenv()


def verify_openai_api_key():
    """Verify that the OpenAI API key is valid."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. Make sure to set it in the .env file."
        )

    # A simple check to see if the key is properly formatted
    if not api_key.startswith(("sk-", "OPENAI-")):
        print("Warning: Your OpenAI API key doesn't seem to have the expected format.")

    return api_key


# Get API key from environment and verify it
OPENAI_API_KEY = verify_openai_api_key()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Process images for AI analysis")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="sample_images",
        help="Directory containing images to process",
    )
    parser.add_argument(
        "--image_output_dir",
        type=str,
        default="processed_images",
        help="Directory for saving processed images",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="results/analysis_results",
        help="Directory for saving processed images",
    )
    parser.add_argument(
        "--resize_width", type=int, default=1024, help="Width to resize images to"
    )
    parser.add_argument(
        "--resize_height", type=int, default=1024, help="Height to resize images to"
    )
    parser.add_argument(
        "--preserve_aspect_ratio",
        type=bool,
        default=True,
        help="Whether to preserve the aspect ratio when resizing",
    )
    parser.add_argument(
        "--recursive",
        type=bool,
        default=True,
        help="Whether to search for images recursively in subdirectories",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=300,
        help="Maximum number of tokens for OpenAI response",
    )
    return parser.parse_args()


def find_images(input_dir, recursive=True):
    """Find all image files in the input directory."""
    valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

    image_files = []
    if recursive:
        for ext in valid_extensions:
            image_files.extend(glob.glob(f"{input_dir}/**/*{ext}", recursive=True))
            image_files.extend(
                glob.glob(f"{input_dir}/**/*{ext.upper()}", recursive=True)
            )
    else:
        for ext in valid_extensions:
            image_files.extend(glob.glob(f"{input_dir}/*{ext}"))
            image_files.extend(glob.glob(f"{input_dir}/*{ext.upper()}"))

    return sorted(image_files)


def resize_image(image_path, width, height, preserve_aspect_ratio=True):
    """Resize an image to the specified dimensions, optionally preserving aspect ratio.
    Images smaller than the target dimensions won't be resized."""
    try:
        img = Image.open(image_path)
        # If image has alpha channel (transparency), convert to RGB
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        original_width, original_height = img.size

        # Check if the image is already smaller than the target dimensions
        if original_width <= width and original_height <= height:
            return img

        if preserve_aspect_ratio:
            # Calculate the new dimensions while preserving aspect ratio
            ratio = min(width / original_width, height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Create a new image with the target dimensions and paste the resized image
            new_img = Image.new("RGB", (width, height), (255, 255, 255))
            paste_x = (width - new_width) // 2
            paste_y = (height - new_height) // 2
            new_img.paste(img, (paste_x, paste_y))
            return new_img
        else:
            # Resize without preserving aspect ratio
            img = img.resize((width, height), Image.LANCZOS)
            return img
    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")
        return None


def encode_image_to_base64(img):
    """Encode a PIL Image to base64."""
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def save_base64_to_file(base64_string, output_path):
    """Save a base64 encoded image to a file."""
    try:
        image_data = base64.b64decode(base64_string)
        with open(output_path, "wb") as f:
            f.write(image_data)
        return True
    except Exception as e:
        print(f"Error saving base64 to file: {e}")
        return False


def analyze_image_with_openai(base64_image, prompt):
    """Analyze an image using OpenAI's Responses API."""
    try:
        response = client.responses.create(
            model="gpt-4o",
            input={
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low",
                    },
                ],
            },
            text={
                "format": {
                    "type": "json_schema",
                    "name": "image_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "architectural_style": {
                                "type": "string",
                                "description": "The architectural style of the image",
                            },
                            "color_palette": {
                                "type": "string",
                                "description": "The color palette of the image",
                            },
                            "futuristic_elements": {
                                "type": "string",
                                "description": "The futuristic elements of the image",
                            },
                            "dominant_materials": {
                                "type": "string",
                                "description": "The dominant materials of the architecture in the image",
                            },
                            "mood": {
                                "type": "string",
                                "description": "The overall mood or tone of the image",
                            },
                            "short_descriptive_label": {
                                "type": "string",
                                "description": "A short descriptive label for clustering",
                            },
                        },
                        "required": [
                            "architectural_style",
                            "color_palette",
                            "futuristic_elements",
                            "short_descriptive_label",
                            "dominant_materials",
                            "mood",
                        ],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
        )
        return response.output_text
    except Exception as e:
        print(f"Error analyzing image with OpenAI: {e}")
        return str(e)


def save_processed_image(img, original_path, image_output_dir, input_dir):
    """Save the processed image to the output directory with a similar path structure."""
    # Create relative path that preserves directory structure
    relative_path = os.path.relpath(original_path, start=input_dir)
    output_path = os.path.join(image_output_dir, relative_path)

    # Create any necessary directories
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the image
    img.save(output_path, format="JPEG")
    return output_path


def main():
    """Main function to process images."""
    args = parse_arguments()

    # Create output directories if they don't exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.image_output_dir, exist_ok=True)

    # Find all images in the input directory
    image_files = find_images(args.input_dir, args.recursive)
    print(f"Found {len(image_files)} images to process.")

    # Prepare results list
    results = []

    # Process each image
    for i, image_path in enumerate(image_files):
        # Clear progress message with specific format for the Streamlit app to detect
        print(f"Processing image {i+1}/{len(image_files)}: {image_path}")

        # Resize image
        img = resize_image(
            image_path,
            args.resize_width,
            args.resize_height,
            args.preserve_aspect_ratio,
        )
        if img is None:
            print(f"Skipping {image_path} due to processing error.")
            continue

        # Save processed image
        processed_path = save_processed_image(
            img, image_path, args.image_output_dir, args.input_dir
        )

        # Encode image to base64
        base64_image = encode_image_to_base64(img)

        analysis_prompt = "You are an expert at image analysis related to urban design and architecture. You are given an image of an urban scene and you need to provide insights on the architectural style, color palette, futuristic elements, archetypes, and a short descriptive label for clustering. The insights should be converted into the given structure. "

        # Analyze image with OpenAI
        print(f"Analyzing image with OpenAI...")
        analysis = analyze_image_with_openai(base64_image, analysis_prompt)

        # Indicate completion of this image - this is tracked by the progress bar
        print(f"Completed analysis for: {os.path.basename(image_path)}")

        # Store results
        results.append(
            {
                "original_path": image_path,
                "processed_path": processed_path,
                # "base64_path": base64_path,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Save intermediate results after each image
        with open(os.path.join(args.output_dir, "analysis_results.json"), "w") as f:
            json.dump(results, f, indent=2)

        # Add a small delay to avoid rate limiting
        time.sleep(1)

    print(f"Processed {len(results)} images successfully.")
    print(f"Results saved to {os.path.join(args.output_dir, 'analysis_results.json')}")


if __name__ == "__main__":
    main()
