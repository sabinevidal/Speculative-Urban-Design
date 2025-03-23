import streamlit as st
import os
import json
import subprocess
import glob
from PIL import Image

st.set_page_config(
    page_title="Image Processing & Analysis",
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


# Function to get a sample of images from a folder
def get_sample_images(folder_path, sample_size=3):
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
    images = []

    for ext in image_extensions:
        images.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
        images.extend(glob.glob(os.path.join(folder_path, f"*{ext.upper()}")))

    if not images:
        return []

    # Take the first few images
    return sorted(images)[:sample_size]


# Function to run a Python script via subprocess
def run_script(script_path, args=None):
    cmd = ["python", script_path]
    if args:
        cmd.extend(args)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    # For image processor, track progress
    if script_path == "image_processor.py":
        # Count total images to process
        total_images = 0
        for root, _, files in os.walk("sample_images"):
            for file in files:
                if file.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")
                ):
                    total_images += 1

        if total_images == 0:
            st.warning("No images found to process.")
            return False

        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Starting image processing...")

        # Process tracking variables
        processed_count = 0
        current_image = ""

        # Read output in real-time
        for line in iter(process.stdout.readline, ""):
            # Check for processing indicators in the output
            if "Processing image" in line:
                try:
                    parts = line.split(":")
                    if len(parts) > 1:
                        current_image = parts[1].strip()
                        status_text.text(f"Processing: {current_image}")
                except:
                    pass

            # Check for completion of an image
            if "Completed analysis for:" in line:
                processed_count += 1
                # Update progress bar
                progress = min(processed_count / total_images, 1.0)
                progress_bar.progress(progress)
                status_text.text(
                    f"Processed {processed_count}/{total_images} images - Current: {current_image}"
                )

        # Read any error output
        stderr = process.stderr.read()

        # Wait for process to complete
        process.wait()

        if process.returncode != 0:
            st.error(f"Error running {script_path}: {stderr}")
            return False

        # Set progress to 100% when done
        progress_bar.progress(1.0)
        status_text.text(
            f"Completed processing {processed_count}/{total_images} images"
        )
        return True
    elif script_path == "cluster_analysis.py":
        # For cluster analysis, show a simpler progress indicator
        status_text = st.empty()
        status_text.text("Running cluster analysis...")

        # Read output in real-time
        for line in iter(process.stdout.readline, ""):
            if "Loading" in line or "Extracting" in line or "Performing" in line:
                status_text.text(line.strip())

        # Read any error output
        stderr = process.stderr.read()

        # Wait for process to complete
        process.wait()

        if process.returncode != 0:
            st.error(f"Error running {script_path}: {stderr}")
            return False

        status_text.text("Cluster analysis completed!")
        return True
    else:
        # For other scripts, use standard approach
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            st.error(f"Error running {script_path}: {stderr}")
            return False

        return True


# Main content
st.header("Image Processing & Analysis")

# Get list of movie folders
with st.spinner("Loading movie folders..."):
    movie_folders = [
        d
        for d in os.listdir("sample_images")
        if os.path.isdir(os.path.join("sample_images", d))
    ]

st.subheader("Available Movie Folders")

# Display a sample of images from each movie folder
for folder in movie_folders:
    with st.expander(f"{folder.replace('_', ' ')}"):
        folder_path = os.path.join("sample_images", folder)

        # Add loading state while fetching sample images
        with st.spinner(f"Loading images from {folder.replace('_', ' ')}..."):
            sample_images = get_sample_images(folder_path)

        if sample_images:
            cols = st.columns(min(3, len(sample_images)))
            for i, img_path in enumerate(sample_images):
                img, error = safe_open_image(img_path)
                if img:
                    cols[i].image(
                        img,
                        caption=os.path.basename(img_path),
                        use_container_width=True,
                    )
                else:
                    cols[i].error(error)
        else:
            st.write("No images found in this folder.")

# Image Processing Section
st.subheader("Step 1: Process Images")

# Count total images in all folders
total_images = 0
for root, _, files in os.walk("sample_images"):
    for file in files:
        if file.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")
        ):
            total_images += 1

st.info(f"Found {total_images} images in sample folders that will be processed.")

if st.button("Process Images"):
    # The run_script function now handles the progress bar and spinner
    success = run_script("image_processor.py")
    if success:
        st.success("Images processed successfully!")

# Display Analysis Results if they exist
with st.spinner("Loading analysis results..."):
    analysis_results = load_json_if_exists(
        "results/analysis_results/analysis_results.json"
    )

if analysis_results:
    st.subheader("Image Analysis Results")

    with st.spinner("Loading analysis samples..."):
        num_samples = min(5, len(analysis_results))
        for i in range(num_samples):
            with st.expander(
                f"Image {i+1}: {os.path.basename(analysis_results[i]['original_path'])}"
            ):
                col1, col2 = st.columns([1, 2])

                # Display the image
                processed_path = analysis_results[i]["processed_path"]
                img, error = safe_open_image(processed_path)
                if img:
                    col1.image(img, use_container_width=True)
                elif error:
                    col1.error(error)

                # Display the analysis
                col2.json(json.loads(analysis_results[i]["analysis"]))

    # Cluster Analysis Section
    st.subheader("Step 2: Cluster Analysis")

    # Number of clusters selection
    n_clusters = st.slider(
        "Number of Clusters",
        min_value=2,
        max_value=10,
        value=5,
        help="Select the number of clusters for K-means clustering",
    )

    if st.button("Run Cluster Analysis"):
        # The run_script function now handles progress tracking
        success = run_script("cluster_analysis.py", ["--n_clusters", str(n_clusters)])
        if success:
            st.success("Cluster analysis completed!")

    # Display cluster results if they exist
    with st.spinner("Loading cluster analysis results..."):
        cluster_results = load_json_if_exists(
            "results/cluster_results/cluster_analysis_results.json"
        )

    if cluster_results:
        st.subheader("Cluster Analysis Results")

        # Replace expander with a heading
        st.write("### Cluster Details")
        with st.spinner("Loading cluster details..."):
            for cluster_id, cluster_info in cluster_results.items():
                with st.expander(
                    f"Cluster {cluster_id} ({cluster_info['size']} images)"
                ):
                    # Display attributes
                    st.write("**Common Styles:**")
                    st.write(", ".join(cluster_info.get("common_styles", ["None"])[:5]))

                    st.write("**Common Elements:**")
                    st.write(
                        ", ".join(cluster_info.get("common_elements", ["None"])[:5])
                    )

                    st.write("**Common Materials:**")
                    st.write(
                        ", ".join(cluster_info.get("common_materials", ["None"])[:5])
                    )

                    st.write("**Common Moods:**")
                    st.write(", ".join(cluster_info.get("common_moods", ["None"])[:5]))

                    # Display sample images if available
                    if "sample_paths" in cluster_info and cluster_info["sample_paths"]:
                        st.write("**Sample Images:**")
                        cols = st.columns(min(3, len(cluster_info["sample_paths"])))
                        for i, img_path in enumerate(cluster_info["sample_paths"]):
                            # Check if the image exists in processed images folder
                            processed_img_path = os.path.join(
                                "processed_images",
                                os.path.relpath(img_path, "sample_images"),
                            )
                            if os.path.exists(processed_img_path):
                                img_path = processed_img_path

                            img, error = safe_open_image(img_path)
                            if img:
                                cols[i].image(
                                    img,
                                    caption=os.path.basename(img_path),
                                    use_container_width=True,
                                )
                            elif error and i < len(cols):
                                cols[i].error(error)

        # Display visualization images
        cluster_viz_path = "results/cluster_results/cluster_visualization.png"
        feature_importance_path = "results/cluster_results/feature_importance.png"

        if os.path.exists(cluster_viz_path) and os.path.exists(feature_importance_path):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Cluster Visualization")
                if os.path.exists(cluster_viz_path):
                    st.image(cluster_viz_path, use_container_width=True)
                else:
                    st.error(
                        f"Cluster visualization image not found at {cluster_viz_path}"
                    )

            with col2:
                st.subheader("Feature Importance")
                if os.path.exists(feature_importance_path):
                    st.image(feature_importance_path, use_container_width=True)
                else:
                    st.error(
                        f"Feature importance image not found at {feature_importance_path}"
                    )

        # Navigation suggestion
        if cluster_results:
            st.info(
                "Now that you have completed the cluster analysis, you can move on to 'Generate Prompts' in the sidebar."
            )
