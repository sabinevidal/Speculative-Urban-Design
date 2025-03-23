#!/usr/bin/env python3
import os
import argparse
import base64
import json
import glob
from io import BytesIO
from datetime import datetime
import time
import logging

from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Valid image extensions
VALID_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

# Default analysis prompt
DEFAULT_ANALYSIS_PROMPT = """
You are an expert at image analysis related to urban design and architecture.
You are given an image of an urban scene and you need to provide insights on the
architectural style, color palette, futuristic elements, dominant materials,
mood, and a short descriptive label for clustering.
The insights should be converted into the given structure.
"""


class ImageProcessor:
    """Class for processing and analyzing images with OpenAI."""

    def __init__(self, api_key=None, model="gpt-4o"):
        """Initialize the image processor with OpenAI API key and model."""
        self.api_key = api_key or self._verify_openai_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def _verify_openai_api_key(self):
        """Verify that the OpenAI API key is valid."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. Make sure to set it in the .env file."
            )

        # A simple check to see if the key is properly formatted
        if not api_key.startswith(("sk-", "OPENAI-")):
            logger.warning(
                "Warning: Your OpenAI API key doesn't seem to have the expected format."
            )

        return api_key

    def find_images(self, input_dir, recursive=True):
        """Find all image files in the input directory."""
        image_files = []
        if recursive:
            for ext in VALID_EXTENSIONS:
                image_files.extend(glob.glob(f"{input_dir}/**/*{ext}", recursive=True))
                image_files.extend(
                    glob.glob(f"{input_dir}/**/*{ext.upper()}", recursive=True)
                )
        else:
            for ext in VALID_EXTENSIONS:
                image_files.extend(glob.glob(f"{input_dir}/*{ext}"))
                image_files.extend(glob.glob(f"{input_dir}/*{ext.upper()}"))

        return sorted(image_files)

    def resize_image(self, image_path, width, height, preserve_aspect_ratio=True):
        """Resize an image to the specified dimensions, optionally preserving aspect ratio."""
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
            logger.error(f"Error resizing image {image_path}: {e}")
            return None

    def encode_image_to_base64(self, img):
        """Encode a PIL Image to base64."""
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=90)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def save_processed_image(self, img, original_path, output_dir, input_dir):
        """Save the processed image to the output directory with a similar path structure."""
        # Create relative path that preserves directory structure
        relative_path = os.path.relpath(original_path, start=input_dir)
        output_path = os.path.join(output_dir, relative_path)

        # Create any necessary directories
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save the image
        img.save(output_path, format="JPEG", quality=90)
        return output_path

    def analyze_image_with_openai(self, base64_image):
        """Analyze an image using OpenAI's Responses API."""
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": DEFAULT_ANALYSIS_PROMPT},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high",
                            },
                        ],
                    },
                ],
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
            logger.error(f"Error analyzing image with OpenAI: {e}")
            return json.dumps(
                {
                    "error": str(e),
                    "architectural_style": "Error",
                    "color_palette": "Error",
                    "futuristic_elements": "Error",
                    "dominant_materials": "Error",
                    "mood": "Error",
                    "short_descriptive_label": "Error in processing",
                }
            )

    def process_images(
        self,
        input_dir,
        output_dir,
        image_output_dir,
        width=1024,
        height=1024,
        preserve_aspect_ratio=True,
        recursive=True,
        prompt=DEFAULT_ANALYSIS_PROMPT,
    ):
        """Process all images in the input directory and save results."""
        # Create output directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(image_output_dir, exist_ok=True)

        # Find all images in the input directory
        image_files = self.find_images(input_dir, recursive)
        logger.info(f"Found {len(image_files)} images to process.")
        print(f"Found {len(image_files)} images to process.")

        # Load existing results if any
        results_path = os.path.join(output_dir, "analysis_results.json")
        results = []
        if os.path.exists(results_path):
            try:
                with open(results_path, "r") as f:
                    results = json.load(f)
                logger.info(f"Loaded {len(results)} existing results.")

                # Get already processed images
                processed_paths = {r["original_path"] for r in results}
                # Filter out already processed images
                image_files = [img for img in image_files if img not in processed_paths]
                logger.info(
                    f"After filtering, {len(image_files)} images remain to be processed."
                )
            except Exception as e:
                logger.error(f"Error loading existing results: {e}")

        # Process each image
        for i, image_path in enumerate(image_files):
            try:
                # Report progress
                print(f"Processing image {i+1}/{len(image_files)}: {image_path}")
                logger.info(f"Processing image {i+1}/{len(image_files)}: {image_path}")

                # Resize image
                img = self.resize_image(
                    image_path, width, height, preserve_aspect_ratio
                )
                if img is None:
                    logger.warning(f"Skipping {image_path} due to processing error.")
                    print(f"Skipping {image_path} due to processing error.")
                    continue

                # Save processed image
                processed_path = self.save_processed_image(
                    img, image_path, image_output_dir, input_dir
                )

                # Encode image to base64
                base64_image = self.encode_image_to_base64(img)

                # Analyze image with OpenAI
                logger.info(f"Analyzing image with OpenAI...")
                print(f"Analyzing image with OpenAI...")
                analysis = self.analyze_image_with_openai(base64_image, prompt)

                # Indicate completion of this image
                print(f"Completed analysis for: {os.path.basename(image_path)}")
                logger.info(f"Completed analysis for: {os.path.basename(image_path)}")

                # Store results
                results.append(
                    {
                        "original_path": image_path,
                        "processed_path": processed_path,
                        "analysis": analysis,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Save intermediate results after each image
                with open(results_path, "w") as f:
                    json.dump(results, f, indent=2)

                # Add a small delay to avoid rate limiting
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                print(f"Error processing image {image_path}: {e}")

        logger.info(f"Processed {len(results)} images successfully.")
        print(f"Processed {len(results)} images successfully.")
        print(f"Results saved to {results_path}")

        return results


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
        help="Directory for saving analysis results",
    )
    parser.add_argument(
        "--resize_width", type=int, default=1024, help="Width to resize images to"
    )
    parser.add_argument(
        "--resize_height", type=int, default=1024, help="Height to resize images to"
    )
    parser.add_argument(
        "--preserve_aspect_ratio",
        action="store_true",
        default=True,
        help="Whether to preserve the aspect ratio when resizing",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Whether to search for images recursively in subdirectories",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="OpenAI model to use for analysis",
    )
    return parser.parse_args()


def main():
    """Main function to process images."""
    args = parse_arguments()

    try:
        # Initialize the image processor
        processor = ImageProcessor(model=args.model)

        # Process images
        processor.process_images(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            image_output_dir=args.image_output_dir,
            width=args.resize_width,
            height=args.resize_height,
            preserve_aspect_ratio=args.preserve_aspect_ratio,
            recursive=args.recursive,
        )
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
