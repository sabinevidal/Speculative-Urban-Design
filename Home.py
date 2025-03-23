import streamlit as st
import os
import json
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


# Main app
def main():
    # Ensure directories and files are set up properly
    try:
        from urban_future_generator import setup_directories

        setup_directories()
    except ImportError:
        pass  # Skip if not available

    st.title("Speculative Urban Future Generator")

    st.markdown(
        """
    ## Welcome to the Speculative Urban Future Generator

    This tool helps you analyze urban design elements from images, create design concepts,
    and generate speculative urban future visualizations.

    ### How to use this tool:

    1. **Image Processing & Analysis**: Process image datasets and analyze their visual elements
    2. **Generate Prompts**: Create prompts for design concepts based on analysis
    3. **Speculative Urban Future Generator**: Generate new urban future images using AI
    4. **Speculative Urban Future Gallery**: View and explore all previously generated urban future images

    Use the sidebar to navigate between these sections.
    """
    )

    # Display sample image or recent results if available
    latest_results = load_json_if_exists(
        "results/urban_future/urban_future_metadata.json"
    )
    if latest_results and len(latest_results) > 0:
        st.subheader("Recent Speculative Urban Future Generation")
        latest = latest_results[-1]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original Street View**")
            orig_img, error = safe_open_image(latest["original_image"])
            if orig_img:
                st.image(orig_img, use_container_width=True)
            elif error:
                st.error(error)

        with col2:
            st.markdown("**Transformed Urban Future**")
            if latest["transformed_images"] and len(latest["transformed_images"]) > 0:
                img, error = safe_open_image(latest["transformed_images"][0])
                if img:
                    st.image(img, use_container_width=True)
                elif error:
                    st.error(error)
            else:
                st.warning("No transformed image available.")


if __name__ == "__main__":
    main()
