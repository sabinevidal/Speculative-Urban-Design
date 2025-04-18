import streamlit as st
import os
import json
import subprocess
from PIL import Image

st.set_page_config(
    page_title="Speculative Urban Future Generator",
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


# Function to list all image files in the streetview_images directory
def get_available_streetview_images():
    images = []
    streetview_dir = "streetview_images"
    if os.path.exists(streetview_dir):
        for file in os.listdir(streetview_dir):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                images.append(file)
    return images


# Function to ensure required directories exist
def setup_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs("results/urban_future", exist_ok=True)


# Main content
st.header("Speculative Urban Future Generator")
st.write("Generate speculative urban future concepts using Street View images and AI.")

# Ensure directories exist
setup_directories()

# Load available prompts for the dropdown
with st.spinner("Loading available prompts..."):
    from urban_future_generator import (
        get_available_prompt_names,
        get_available_prompt_ids,
        get_prompt_by_name,
        load_cluster_prompts,
        setup_directories,
    )

    # Import the directory_utils for metadata handling
    import sys

    sys.path.append(".")  # Ensure the root directory is in the path
    from directory_utils import load_metadata

    # Ensure directories and files are set up properly
    setup_directories()

    available_prompts = get_available_prompt_ids()
    prompt_names = get_available_prompt_names()
    # Create a mapping from cluster ID to prompt name
    prompt_name_mapping = {}
    prompts_data = load_cluster_prompts()
    if prompts_data:
        prompt_name_mapping = {
            cluster_id: data["name"] for cluster_id, data in prompts_data.items()
        }

# Initialize state variables
if "street_view_image" not in st.session_state:
    st.session_state.street_view_image = None

# Create two columns for the layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Step 1: Select Street View Image")

    # Get available streetview images
    available_images = get_available_streetview_images()

    if available_images:
        # Create a dropdown to select an image
        selected_image = st.selectbox(
            "Select a street view image",
            available_images,
            format_func=lambda x: x.replace("-", " ").replace("_", " ").split(".")[0],
            help="Choose from available street view images",
        )

        # Set the selected image as the current street view image
        if selected_image:
            image_path = os.path.join("streetview_images", selected_image)
            st.session_state.street_view_image = image_path

            # Display the selected image
            img, error = safe_open_image(image_path)
            if img:
                st.image(
                    img,
                    caption=f"Selected Image: {selected_image}",
                    width=None,
                )
            elif error:
                st.error(error)
    else:
        st.warning("No street view images found in the 'streetview_images' directory.")

with col2:
    st.subheader("Step 2: Choose Design Concept")

    # Allow user to select a prompt from available ones
    if available_prompts:
        selected_prompt = st.selectbox(
            "Select a design concept prompt",
            available_prompts,
            format_func=lambda x: prompt_name_mapping.get(x, x),
            help="Choose from pre-generated design concept prompts",
        )
        # Preview the selected prompt
        prompt_text = get_prompt_by_name(selected_prompt)
        st.write(f"**Prompt:** {prompt_text}")
    else:
        st.warning("No design concept prompts found. Default prompt will be used.")
        selected_prompt = None

    # Transformation strength slider
    strength = st.slider(
        "Transformation Strength",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="How strongly to transform the image. Higher values create more dramatic changes (0.5: preserve more of original, 0.9: more creative freedom)",
    )

# Show the generate button only if we have a street view image
if st.session_state.street_view_image:
    st.subheader("Step 3: Generate an Image of an Urban Future")

    if st.button("Generate Urban Future Image", use_container_width=True):
        with st.spinner("Generating urban future image..."):
            from urban_future_generator import transform_street_view

            # Transform the street view image
            transform_result = transform_street_view(
                st.session_state.street_view_image,
                get_prompt_by_name(selected_prompt),
                strength,
                prompt_name=selected_prompt,
            )

            if transform_result["success"]:
                st.success("Successfully generated urban future image!")

                # Display the results
                cols = st.columns(2)

                with cols[0]:
                    st.markdown("**Original Street View**")
                    orig_img, error = safe_open_image(
                        transform_result["original_image"]
                    )
                    if orig_img:
                        st.image(orig_img, width=None)
                    elif error:
                        st.error(error)

                with cols[1]:
                    st.markdown("**Transformed Urban Future Image**")
                    st.write(f"**Prompt:** {transform_result['prompt']}")

                    # Display first transformed image
                    if transform_result["transformed_images"]:
                        img_path = transform_result["transformed_images"][0]
                        img, error = safe_open_image(img_path)
                        if img:
                            st.image(img, width=None)
                        elif error:
                            st.error(error)
                    else:
                        st.warning("No transformed image was generated.")

                # Show additional variations if available
                if len(transform_result["transformed_images"]) > 1:
                    st.markdown("**Additional Design Variations:**")
                    variation_cols = st.columns(
                        min(3, len(transform_result["transformed_images"]) - 1)
                    )

                    for j, img_path in enumerate(
                        transform_result["transformed_images"][1:]
                    ):
                        idx = j % len(variation_cols)
                        img, error = safe_open_image(img_path)
                        if img:
                            variation_cols[idx].image(img, width=None)
                        elif error:
                            variation_cols[idx].error(error)
            else:
                st.error(
                    f"Error generating urban future image: {transform_result['error']}"
                )

# Display previously generated results at the bottom
with st.spinner("Loading previous urban future images..."):
    # Use the load_metadata function from directory_utils
    urban_future_metadata = load_metadata()

if urban_future_metadata:
    with st.expander("View Previous Urban Future Image Generations", expanded=False):
        st.subheader("Previous Urban Future Image Generations")

        # Show the most recent 5 designs
        for i, result in enumerate(urban_future_metadata[-5:]):
            # Extract a display name from the original image path
            img_path = result.get("original_image", "Unknown")
            display_name = (
                os.path.basename(img_path)
                .split(".")[0]
                .replace("-", " ")
                .replace("_", " ")
            )

            with st.expander(f"{display_name} ({result.get('timestamp', 'Unknown')})"):
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.markdown("**Original Street View**")
                    orig_img, error = safe_open_image(img_path)
                    if orig_img:
                        st.image(orig_img, width=None)
                    elif error:
                        st.error(error)

                with col2:
                    st.markdown("**Transformed Urban Future Images**")
                    st.write(f"**Prompt:** {result['prompt']}")

                    # If there are multiple transformed images, show them in columns
                    if len(result["transformed_images"]) > 0:
                        cols = st.columns(min(2, len(result["transformed_images"])))
                        for j, img_path in enumerate(result["transformed_images"]):
                            if j < len(
                                cols
                            ):  # Ensure we don't exceed the number of columns
                                img, error = safe_open_image(img_path)
                                if img:
                                    cols[j].image(img, width=None)
                                elif error:
                                    cols[j].error(error)
