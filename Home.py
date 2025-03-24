import streamlit as st
import os
import json
from PIL import Image

# Set page configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="Speculative Urban Future Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Function to safely check if an image exists and can be opened
def safe_open_image(img_path):
    if img_path is None:
        return None, "Image path is None"
    if not os.path.exists(img_path):
        return None, f"Image file not found: {os.path.basename(img_path)}"
    try:
        img = Image.open(img_path)
        # Convert to RGB if needed to avoid mode errors
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            # Create a white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            # Paste the image on the background
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Validate image
        img.verify()  # Verify that it's a valid image
        # Need to reopen after verify
        img = Image.open(img_path)
        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

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

    API keys for OpenAI and Stability AI are provided - please use responsibly!
    """
    )

    # Display sample image or recent results if available
    latest_results = load_json_if_exists(
        "results/urban_future/urban_future_metadata.json"
    )

    # Validate the JSON data before using it
    if latest_results and isinstance(latest_results, list) and len(latest_results) > 0:
        try:
            st.subheader("Recent Speculative Urban Future Generation")
            latest = latest_results[-1]

            # Validate that latest has the expected structure
            if not isinstance(latest, dict):
                st.warning("Invalid data format in urban_future_metadata.json")
                return

            # Check if required keys exist
            if "original_image" not in latest:
                st.warning("No original image information found in the metadata")
                return

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Original Street View**")
                if not isinstance(latest["original_image"], str):
                    st.warning("Invalid original image path")
                else:
                    orig_img, error = safe_open_image(latest["original_image"])
                    if orig_img is not None and hasattr(orig_img, "size"):
                        try:
                            st.image(orig_img, width=None)
                        except Exception as e:
                            st.error(f"Error displaying image: {str(e)}")
                    elif error:
                        st.error(error)
                    else:
                        st.warning("Cannot display original image")

            with col2:
                st.markdown("**Transformed Urban Future**")
                if (
                    "transformed_images" not in latest
                    or not latest["transformed_images"]
                ):
                    st.warning("No transformed images found")
                elif not isinstance(latest["transformed_images"], list):
                    st.warning("Invalid transformed images format")
                elif len(latest["transformed_images"]) > 0:
                    if not isinstance(latest["transformed_images"][0], str):
                        st.warning("Invalid transformed image path")
                    else:
                        img, error = safe_open_image(latest["transformed_images"][0])
                        if img is not None and hasattr(img, "size"):
                            try:
                                st.image(img, width=None)
                            except Exception as e:
                                st.error(f"Error displaying image: {str(e)}")
                        elif error:
                            st.error(error)
                        else:
                            st.warning("Cannot display transformed image")
                else:
                    st.warning("No transformed image available.")
        except Exception as e:
            st.error(f"Error processing results: {str(e)}")
    elif latest_results is not None:
        st.info("No urban future generations found. Try generating some first!")
    else:
        st.info("No results file found. Try generating some urban futures first!")


if __name__ == "__main__":
    main()
