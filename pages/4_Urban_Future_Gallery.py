import streamlit as st
import os
import json
from PIL import Image

st.set_page_config(
    page_title="Speculative Urban Future Gallery",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Function to safely check if an image exists and can be opened
def safe_open_image(img_path):
    if not os.path.exists(img_path):
        return None, f"Image file not found: {os.path.basename(img_path)}"
    try:
        img = Image.open(img_path)
        return img, None
    except Exception as e:
        return None, f"Error opening image: {str(e)}"


# Function to load JSON data if it exists
def load_json_if_exists(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                content = f.read().strip()
                if not content:  # File exists but is empty or just whitespace
                    return []
                try:
                    data = json.loads(content)
                    return data
                except json.JSONDecodeError as e:
                    print(f"Error loading JSON file {file_path}: {e}")
                    return []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    return None


# Function to find all image files in the urban future results directory
def find_all_urban_future_images():
    """Find all images in the urban future results directory"""
    results_dir = "results/urban_future"
    image_files = []

    # Get metadata using the directory_utils loader
    metadata = load_metadata()

    # Build a set of images already in metadata to avoid duplicates
    metadata_images = set()
    for entry in metadata:
        if "transformed_images" in entry:
            for img in entry["transformed_images"]:
                metadata_images.add(img)

    # Scan for images not in metadata
    if os.path.exists(results_dir):
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg")):
                    full_path = os.path.join(root, file)
                    if full_path not in metadata_images:
                        # Try to determine the original image from directory name
                        dir_name = os.path.basename(root)
                        image_files.append(
                            {
                                "timestamp": "Unknown",
                                "original_image": f"streetview_images/{dir_name}.jpg",
                                "transformed_images": [full_path],
                                "prompt": "Unknown (Image found outside metadata)",
                                "prompt_name": "Unknown",
                            }
                        )

    return image_files


# Main content
st.header("Speculative Urban Future Gallery")
st.write("View all previously generated urban future images.")

# Load the prompt mapping to get prompt names
from urban_future_generator import load_cluster_prompts, setup_directories

# Import directory_utils for metadata handling
import sys

sys.path.append(".")  # Ensure the root directory is in the path
from directory_utils import load_metadata

# Ensure directories and files are set up properly
setup_directories()

# Create a mapping from cluster ID to prompt name
prompt_name_mapping = {}
prompts_data = load_cluster_prompts()
if prompts_data:
    prompt_name_mapping = {
        cluster_id: data["name"] for cluster_id, data in prompts_data.items()
    }

# Load urban future metadata
urban_future_metadata = load_metadata()

# Find all image files not in metadata
unlisted_images = find_all_urban_future_images()

# Combine listed and unlisted images
all_designs = urban_future_metadata + unlisted_images

if not all_designs:
    st.info(
        "No urban future images have been generated yet. Try generating some images in the Speculative Urban Future Generator page."
    )
else:
    # Add filtering options
    col1, col2 = st.columns([1, 3])

    with col1:
        # Extract all unique prompts
        all_prompts = sorted(
            list(set([design.get("prompt_name", "Unknown") for design in all_designs]))
        )

        # Map prompt IDs to names if available
        display_prompts = ["All Designs"]
        for prompt_id in all_prompts:
            if prompt_id in prompt_name_mapping:
                display_prompts.append(prompt_name_mapping[prompt_id])
            else:
                display_prompts.append(prompt_id)

        filter_prompt = st.selectbox(
            "Filter by Design Concept",
            display_prompts,
        )

        # Sort options
        sort_option = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First"],
        )

        # Add option to show only unlisted images
        show_only_unlisted = st.checkbox("Show only unlisted images")

    # Apply filters
    filtered_designs = all_designs

    # Filter by prompt
    if filter_prompt != "All Designs":
        # Find the prompt ID from the name
        prompt_id = None
        for pid, name in prompt_name_mapping.items():
            if name == filter_prompt:
                prompt_id = pid
                break

        # If we found a matching ID, filter by it
        if prompt_id:
            filtered_designs = [
                design
                for design in filtered_designs
                if design.get("prompt_name") == prompt_id
            ]
        else:
            # If no matching ID (maybe we're using the raw ID), filter by the name directly
            filtered_designs = [
                design
                for design in filtered_designs
                if design.get("prompt_name") == filter_prompt
            ]

    # Filter for unlisted images if requested
    if show_only_unlisted:
        filtered_designs = [
            d for d in filtered_designs if d.get("timestamp") == "Unknown"
        ]

    # Sort the designs
    if sort_option == "Newest First":
        filtered_designs = sorted(
            filtered_designs, key=lambda x: x.get("timestamp", ""), reverse=True
        )
    else:
        filtered_designs = sorted(
            filtered_designs, key=lambda x: x.get("timestamp", "")
        )

    # Display the designs
    st.subheader(f"Showing {len(filtered_designs)} Urban Future Images")

    # Group by date for better organization
    for i, design in enumerate(filtered_designs):
        with st.expander(f"{design.get('timestamp', 'Unknown')}"):
            cols = st.columns([1, 2])

            with cols[0]:
                st.markdown("**Original Street View**")
                orig_img, error = safe_open_image(design.get("original_image", ""))
                if orig_img:
                    st.image(orig_img, width=None)
                elif error:
                    st.error(error)

                # Display cluster/prompt info
                prompt_id = design.get("prompt_name", "Unknown")
                prompt_name = prompt_name_mapping.get(prompt_id, prompt_id)
                st.markdown(f"**Design Concept**: {prompt_name}")

            with cols[1]:
                st.markdown("**Generated Urban Future Images**")

                # Show the prompt used
                st.write(f"**Prompt**: {design.get('prompt', 'No prompt specified')}")

                # Display transformed images
                transformed_images = design.get("transformed_images", [])
                if transformed_images:
                    transformed_cols = st.columns(min(2, len(transformed_images)))
                    for j, img_path in enumerate(transformed_images):
                        img, error = safe_open_image(img_path)
                        if img:
                            transformed_cols[j % len(transformed_cols)].image(
                                img, width=None
                            )
                        elif error:
                            transformed_cols[j % len(transformed_cols)].error(error)
                else:
                    st.warning("No transformed images found for this design.")
