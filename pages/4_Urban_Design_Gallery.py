import streamlit as st
import os
import json
from PIL import Image

st.set_page_config(
    page_title="Urban Design Gallery",
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


# Main content
st.header("Urban Design Gallery")
st.write("View all previously generated urban design concepts.")

# Load the prompt mapping to get prompt names
from urban_design_generator import load_cluster_prompts, setup_directories

# Ensure directories and files are set up properly
setup_directories()

# Create a mapping from cluster ID to prompt name
prompt_name_mapping = {}
prompts_data = load_cluster_prompts()
if prompts_data:
    prompt_name_mapping = {
        cluster_id: data["name"] for cluster_id, data in prompts_data.items()
    }

# Load urban design metadata
metadata_path = "results/urban_design/urban_design_metadata.json"
urban_design_metadata = load_json_if_exists(metadata_path)

if not urban_design_metadata:
    st.info(
        "No urban designs have been generated yet. Try generating some designs in the Urban Design Generator page."
    )
else:
    # Add filtering options
    col1, col2 = st.columns([1, 3])

    with col1:
        # Extract all unique locations
        all_locations = sorted(
            list(
                set(
                    [
                        design.get("location", "Unknown")
                        for design in urban_design_metadata
                    ]
                )
            )
        )

        # Add 'All Locations' option
        filter_location = st.selectbox(
            "Filter by Location",
            ["All Locations"] + all_locations,
        )

        # Extract all unique prompts
        all_prompts = sorted(
            list(
                set(
                    [
                        design.get("prompt_name", "Unknown")
                        for design in urban_design_metadata
                    ]
                )
            )
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

    # Apply filters
    filtered_designs = urban_design_metadata

    # Filter by location
    if filter_location != "All Locations":
        filtered_designs = [
            design
            for design in filtered_designs
            if design.get("location") == filter_location
        ]

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
    st.subheader(f"Showing {len(filtered_designs)} Urban Design Concepts")

    # Group by date for better organization
    for i, design in enumerate(filtered_designs):
        with st.expander(
            f"{design.get('location', 'Unknown')} - {design.get('timestamp', 'Unknown')}"
        ):
            cols = st.columns([1, 2])

            with cols[0]:
                st.markdown("**Original Street View**")
                orig_img, error = safe_open_image(design.get("original_image", ""))
                if orig_img:
                    st.image(orig_img, use_container_width=True)
                elif error:
                    st.error(error)

                # Display cluster/prompt info
                prompt_id = design.get("prompt_name", "Unknown")
                prompt_name = prompt_name_mapping.get(prompt_id, prompt_id)
                st.markdown(f"**Design Concept**: {prompt_name}")

            with cols[1]:
                st.markdown("**Generated Urban Design**")

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
                                img, use_container_width=True
                            )
                        elif error:
                            transformed_cols[j % len(transformed_cols)].error(error)
                else:
                    st.warning("No transformed images found for this design.")
