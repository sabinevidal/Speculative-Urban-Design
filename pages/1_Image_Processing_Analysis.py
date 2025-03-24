import streamlit as st
import os
import json
import glob
import sys
import time
import threading
from pathlib import Path
from PIL import Image
import queue

# Add the root directory to Python path to allow module imports
sys.path.append(str(Path(__file__).parent.parent))

# Page configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="Image Processing & Analysis for Urban Futures",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏙️",
)

# Import the ImageProcessor from image_processor module
try:
    from image_processor import (
        ImageProcessor,
        VALID_EXTENSIONS,
        DEFAULT_ANALYSIS_PROMPT,
    )
except ImportError:
    st.error(
        "Failed to import ImageProcessor module. Make sure image_processor.py is in the root directory."
    )
    VALID_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
    DEFAULT_ANALYSIS_PROMPT = "Analyze this urban scene"

# Apply custom styling
st.markdown(
    """
<style>
    .main .block-container {padding-top: 2rem;}
    .stProgress > div > div > div {background-color: #4CAF50;}
    div[data-testid="stExpander"] div[role="button"] p {font-size: 1.1rem;}
    h1, h2, h3 {margin-bottom: 0.5rem;}
    .stButton>button {width: 100%; background-color: #4CAF50; color: white;}
    .stButton>button:hover {background-color: #45a049;}
</style>
""",
    unsafe_allow_html=True,
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
                    st.error(f"Error loading JSON file {file_path}: {e}")
                    return []
        except Exception as e:
            st.error(f"Error reading file {file_path}: {e}")
            return []
    return None


# Function to get a sample of images from a folder
def get_sample_images(folder_path, sample_size=3):
    images = []
    for ext in VALID_EXTENSIONS:
        images.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
        images.extend(glob.glob(os.path.join(folder_path, f"*{ext.upper()}")))

    if not images:
        return []

    # Take the first few images
    return sorted(images)[:sample_size]


# Function to count images in a directory (including subdirectories)
def count_images_in_directory(directory):
    total_images = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(VALID_EXTENSIONS)):
                total_images += 1
    return total_images


# Function to process images using the ImageProcessor class directly
def process_images(
    input_dir,
    output_dir,
    image_output_dir,
    width,
    height,
    preserve_aspect_ratio,
    recursive,
    progress_bar,
    status_text,
    message_queue,
):
    try:
        # Initialize the image processor
        processor = ImageProcessor()

        # Find all images in the input directory
        image_files = processor.find_images(input_dir, recursive)
        total_images = len(image_files)
        message_queue.put(
            {"type": "info", "message": f"Found {total_images} images to process."}
        )

        # Load existing results if any
        results_path = os.path.join(output_dir, "analysis_results.json")
        results = []
        processed_count = 0

        if os.path.exists(results_path):
            try:
                with open(results_path, "r") as f:
                    results = json.load(f)
                message_queue.put(
                    {
                        "type": "info",
                        "message": f"Loaded {len(results)} existing results.",
                    }
                )

                # Get already processed images
                processed_paths = {r["original_path"] for r in results}
                # Filter out already processed images
                image_files = [img for img in image_files if img not in processed_paths]
                message_queue.put(
                    {
                        "type": "info",
                        "message": f"After filtering, {len(image_files)} images remain to be processed.",
                    }
                )
            except Exception as e:
                message_queue.put(
                    {"type": "error", "message": f"Error loading existing results: {e}"}
                )

        # Create output directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(image_output_dir, exist_ok=True)

        # Process each image
        for i, image_path in enumerate(image_files):
            try:
                # Report progress
                current_image = image_path
                message_queue.put(
                    {
                        "type": "progress",
                        "current_image": current_image,
                        "message": f"Processing image {i+1}/{len(image_files)}: {image_path}",
                    }
                )

                # Resize image
                img = processor.resize_image(
                    image_path, width, height, preserve_aspect_ratio
                )
                if img is None:
                    message_queue.put(
                        {
                            "type": "warning",
                            "message": f"Skipping {image_path} due to processing error.",
                        }
                    )
                    continue

                # Save processed image
                processed_path = processor.save_processed_image(
                    img, image_path, image_output_dir, input_dir
                )

                # Encode image to base64
                base64_image = processor.encode_image_to_base64(img)

                # Analyze image with OpenAI
                message_queue.put(
                    {"type": "info", "message": f"Analyzing image with OpenAI..."}
                )
                analysis = processor.analyze_image_with_openai(base64_image)

                # Indicate completion of this image
                processed_count += 1
                progress = min(processed_count / total_images, 1.0)
                message_queue.put(
                    {
                        "type": "complete",
                        "processed_count": processed_count,
                        "total_images": total_images,
                        "progress": progress,
                        "current_image": os.path.basename(image_path),
                        "message": f"Completed analysis for: {os.path.basename(image_path)}",
                    }
                )

                # Store results
                results.append(
                    {
                        "original_path": image_path,
                        "processed_path": processed_path,
                        "analysis": analysis,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                )

                # Save intermediate results after each image
                with open(results_path, "w") as f:
                    json.dump(results, f, indent=2)

                # Add a small delay to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                message_queue.put(
                    {
                        "type": "error",
                        "message": f"Error processing image {image_path}: {e}",
                    }
                )

        # Processing complete
        message_queue.put(
            {
                "type": "success",
                "message": f"Processed {processed_count} images successfully. Results saved to {results_path}",
            }
        )

    except Exception as e:
        message_queue.put(
            {"type": "error", "message": f"Error in image processing: {e}"}
        )


# Function to run cluster analysis as a subprocess (keep this since we're not refactoring cluster_analysis.py yet)
def run_cluster_analysis(n_clusters):
    import subprocess

    cmd = ["python", "cluster_analysis.py", "--n_clusters", str(n_clusters)]

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
    except Exception as e:
        st.error(f"Failed to start cluster analysis process: {e}")
        return False

    # Show a simpler progress indicator
    status_text = st.empty()
    status_text.info("Running cluster analysis...")

    # Read output in real-time
    for line in iter(process.stdout.readline, ""):
        if "Loading" in line or "Extracting" in line or "Performing" in line:
            status_text.info(line.strip())

    # Read any error output
    stderr = process.stderr.read()

    # Wait for process to complete
    process.wait()

    if process.returncode != 0:
        st.error(f"Error running cluster analysis: {stderr}")
        return False

    status_text.success("Cluster analysis completed!")
    return True


# Main content
st.title("Image Processing & Analysis")
st.markdown("---")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(
    ["Film Folder Browser", "Image Processing", "Analysis Results"]
)

with tab1:
    st.header("Browse Film Folders")

    # Get list of film folders
    with st.spinner("Loading film folders..."):
        if not os.path.exists("sample_images"):
            st.warning(
                "Sample images directory not found. Please create a 'sample_images' directory with film folders."
            )
            film_folders = []
        else:
            film_folders = [
                d
                for d in os.listdir("sample_images")
                if os.path.isdir(os.path.join("sample_images", d))
            ]

    if not film_folders:
        st.warning("No film folders found in the sample_images directory.")
    else:
        # Display a sample of images from each film folder
        st.subheader(f"Found {len(film_folders)} Film Folders")

        for folder in film_folders:
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
                    st.warning("No images found in this folder.")

with tab2:
    st.header("Process Images")

    # Count total images in all folders
    total_images = count_images_in_directory("sample_images")

    if total_images == 0:
        st.warning("No images found in sample folders. Please add images to process.")
    else:
        st.info(
            f"Found {total_images} images in sample folders that will be processed."
        )

        # Check if processing is in progress using session state
        if "processing" not in st.session_state:
            st.session_state.processing = False

        # Create a button to start processing
        process_button = st.button(
            "Process Images",
            use_container_width=True,
            disabled=st.session_state.processing,
        )

        # Progress area (shown only when processing)
        progress_container = st.container()

        resize_width = 1024
        resize_height = 1024
        preserve_aspect_ratio = True
        recursive_search = True

        if process_button:
            with progress_container:
                # Create progress tracking components
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.info("Starting image processing...")

                # Set up a queue for thread communication
                message_queue = queue.Queue()

                # Start processing in a separate thread
                st.session_state.processing = True
                process_thread = threading.Thread(
                    target=process_images,
                    args=(
                        "sample_images",  # input_dir
                        "results/analysis_results",  # output_dir
                        "processed_images",  # image_output_dir
                        resize_width,
                        resize_height,
                        preserve_aspect_ratio,
                        recursive_search,
                        progress_bar,
                        status_text,
                        message_queue,
                    ),
                )
                process_thread.start()

                # Monitor the thread and update the UI
                current_image = ""
                processed_count = 0

                # Process messages from the queue
                while process_thread.is_alive() or not message_queue.empty():
                    try:
                        # Try to get a message from the queue, wait for up to 0.1 seconds
                        message = message_queue.get(timeout=0.1)

                        # Process the message based on its type
                        if message["type"] == "info":
                            status_text.info(message["message"])
                        elif message["type"] == "warning":
                            status_text.warning(message["message"])
                        elif message["type"] == "error":
                            status_text.error(message["message"])
                        elif message["type"] == "success":
                            status_text.success(message["message"])
                        elif message["type"] == "progress":
                            current_image = message["current_image"]
                            status_text.info(
                                f"Processing: {os.path.basename(current_image)}"
                            )
                        elif message["type"] == "complete":
                            processed_count = message["processed_count"]
                            progress_bar.progress(message["progress"])
                            status_text.success(
                                f"Processed {processed_count}/{message['total_images']} images - Current: {message['current_image']}"
                            )

                        # Mark the message as processed
                        message_queue.task_done()

                    except queue.Empty:
                        # No messages received, just continue
                        pass

                    # Add a small delay to avoid hogging the CPU
                    time.sleep(0.1)

                # Processing complete
                progress_bar.progress(1.0)
                st.success("✅ Images processed successfully!")
                st.balloons()

                # Reset the processing flag
                st.session_state.processing = False

                # Navigation suggestion
                st.markdown("---")
                st.success(
                    "Now that you have completed the image processing, you can move on to 'Analysis Results' on the next tab."
                )

with tab3:
    st.header("Analysis Results")

    # Display Analysis Results if they exist
    with st.spinner("Loading analysis results..."):
        analysis_results = load_json_if_exists(
            "results/analysis_results/analysis_results.json"
        )

    if not analysis_results:
        st.info("No analysis results found. Process images first.")
    else:
        # Add filtering options
        st.subheader(f"Found {len(analysis_results)} Analyzed Images")

        # Get unique film folders from results
        film_folders = list(
            set(
                [
                    os.path.dirname(result["original_path"]).split("/")[1]
                    for result in analysis_results
                    if "/" in result["original_path"]
                ]
            )
        )

        # Add filter by film folder
        if film_folders:
            selected_folder = st.selectbox(
                "Filter by Film Folder", ["All Folders"] + film_folders
            )

            # Filter results by selected folder
            if selected_folder != "All Folders":
                filtered_results = [
                    result
                    for result in analysis_results
                    if selected_folder in result["original_path"]
                ]
            else:
                filtered_results = analysis_results
        else:
            filtered_results = analysis_results

        num_samples = min(5, len(filtered_results))
        if num_samples > 0:
            st.subheader("Sample Analysis Results")

            with st.spinner("Loading analysis samples..."):
                for i in range(num_samples):
                    with st.expander(
                        f"Image {i+1}: {os.path.basename(filtered_results[i]['original_path'])}"
                    ):
                        col1, col2 = st.columns([1, 2])

                        # Display the image
                        processed_path = filtered_results[i]["processed_path"]
                        img, error = safe_open_image(processed_path)
                        if img:
                            col1.image(img, use_container_width=True)
                        elif error:
                            col1.error(error)

                        # Display the analysis
                        try:
                            analysis_data = json.loads(filtered_results[i]["analysis"])
                            col2.json(analysis_data)

                            # Display summary of the analysis
                            with col2:
                                st.markdown("### Summary")
                                st.markdown(
                                    f"**Style:** {analysis_data.get('architectural_style', 'N/A')}"
                                )
                                st.markdown(
                                    f"**Materials:** {analysis_data.get('dominant_materials', 'N/A')}"
                                )
                                st.markdown(
                                    f"**Mood:** {analysis_data.get('mood', 'N/A')}"
                                )
                                st.markdown(
                                    f"**Label:** {analysis_data.get('short_descriptive_label', 'N/A')}"
                                )
                        except Exception as e:
                            col2.error(f"Error parsing analysis data: {e}")

        # Cluster Analysis Section
        st.markdown("---")
        st.header("Cluster Analysis")

        # Number of clusters selection
        n_clusters = st.slider(
            "Number of Clusters",
            min_value=2,
            max_value=10,
            value=5,
            help="Select the number of clusters for K-means clustering",
        )

        if st.button("Run Cluster Analysis", use_container_width=True):
            # Run cluster analysis using subprocess (keeping this since we're not refactoring cluster_analysis.py)
            success = run_cluster_analysis(n_clusters)
            if success:
                st.success("✅ Cluster analysis completed!")
                st.balloons()

        # Display cluster results if they exist
        with st.spinner("Loading cluster analysis results..."):
            cluster_results = load_json_if_exists(
                "results/cluster_results/cluster_analysis_results.json"
            )

        if cluster_results:
            st.subheader("Cluster Analysis Results")

            # Replace expander with a heading
            st.markdown("### Cluster Details")

            # Create metric summary at the top
            metric_cols = st.columns(len(cluster_results))
            for i, (cluster_id, cluster_info) in enumerate(cluster_results.items()):
                metric_cols[i].metric(
                    label=f"Cluster {cluster_id}",
                    value=cluster_info["size"],
                    delta=f"{cluster_info['size']/len(analysis_results)*100:.1f}%",
                    help=f"This cluster contains {cluster_info['size']} images",
                )

            with st.spinner("Loading cluster details..."):
                for cluster_id, cluster_info in cluster_results.items():
                    with st.expander(
                        f"Cluster {cluster_id} ({cluster_info['size']} images)"
                    ):
                        # Display attributes
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Common Styles:**")
                            st.markdown(
                                "- "
                                + "\n- ".join(
                                    cluster_info.get("common_styles", ["None"])[:5]
                                )
                            )

                            st.markdown("**Common Elements:**")
                            st.markdown(
                                "- "
                                + "\n- ".join(
                                    cluster_info.get("common_elements", ["None"])[:5]
                                )
                            )

                        with col2:
                            st.markdown("**Common Materials:**")
                            st.markdown(
                                "- "
                                + "\n- ".join(
                                    cluster_info.get("common_materials", ["None"])[:5]
                                )
                            )

                            st.markdown("**Common Moods:**")
                            st.markdown(
                                "- "
                                + "\n- ".join(
                                    cluster_info.get("common_moods", ["None"])[:5]
                                )
                            )

                        # Display sample images if available
                        if (
                            "sample_paths" in cluster_info
                            and cluster_info["sample_paths"]
                        ):
                            st.markdown("---")
                            st.markdown("**Sample Images:**")
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
            st.markdown("---")
            st.subheader("Visualizations")

            cluster_viz_path = "results/cluster_results/cluster_visualization.png"
            feature_importance_path = "results/cluster_results/feature_importance.png"

            if os.path.exists(cluster_viz_path) and os.path.exists(
                feature_importance_path
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Cluster Visualization")
                    if os.path.exists(cluster_viz_path):
                        st.image(cluster_viz_path, use_container_width=True)
                    else:
                        st.error(
                            f"Cluster visualization image not found at {cluster_viz_path}"
                        )

                with col2:
                    st.markdown("#### Feature Importance")
                    if os.path.exists(feature_importance_path):
                        st.image(feature_importance_path, use_container_width=True)
                    else:
                        st.error(
                            f"Feature importance image not found at {feature_importance_path}"
                        )

            # Navigation suggestion
            st.markdown("---")
            st.success(
                "Now that you have completed the cluster analysis, you can move on to 'Generate Prompts' in the sidebar."
            )
