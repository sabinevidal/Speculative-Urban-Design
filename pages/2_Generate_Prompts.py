import streamlit as st
import os
import json
import subprocess
from PIL import Image

st.set_page_config(
    page_title="Generate Cluster Prompts",
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


# Function to run a Python script via subprocess
def run_script(script_path, args=None):
    cmd = ["python", script_path]
    if args:
        cmd.extend(args)
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    if script_path == "generate_cluster_prompts.py":
        # For prompt generation, show progress updates with progress bar
        status_text = st.empty()
        status_text.text("Initializing prompt generation...")
        progress_bar = st.progress(0)

        # Tracking variables
        total_clusters = 0
        processed_clusters = 0
        current_cluster = ""

        # Read output in real-time
        for line in iter(process.stdout.readline, ""):
            # Get total clusters
            if "Found" in line and "clusters to process" in line:
                try:
                    parts = line.split("Found")[1].split("clusters")[0]
                    total_clusters = int(parts.strip())
                    status_text.text(f"Found {total_clusters} clusters to process")
                except:
                    pass

            # Track current cluster being processed
            elif "Generating prompt for cluster" in line:
                try:
                    current_cluster = line.strip()
                    status_text.text(current_cluster)
                except:
                    pass

            # Track completed clusters
            elif "Completed prompt generation for cluster" in line:
                processed_clusters += 1
                if total_clusters > 0:
                    progress = min(processed_clusters / total_clusters, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(
                        f"Processed {processed_clusters}/{total_clusters} clusters"
                    )

            # Final completion message
            elif "Prompts have been generated" in line:
                progress_bar.progress(1.0)

        # Read any error output
        stderr = process.stderr.read()

        # Wait for process to complete
        process.wait()

        if process.returncode != 0:
            st.error(f"Error running {script_path}: {stderr}")
            return False

        status_text.text("Prompt generation completed!")
        return True
    else:
        # For other scripts, use standard approach
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            st.error(f"Error running {script_path}: {stderr}")
            return False

        return True


# Main content
st.header("Generate Cluster Prompts")

# Check if cluster analysis has been completed
cluster_results = load_json_if_exists(
    "results/cluster_results/cluster_analysis_results.json"
)
if not cluster_results:
    st.warning(
        "You need to run the cluster analysis first. Please go to the 'Image Processing & Analysis' page."
    )
else:
    st.info(
        f"Found {len(cluster_results)} clusters from the analysis. Ready to generate prompts."
    )

    if st.button("Generate Prompts for Clusters"):
        # The run_script function handles progress tracking
        success = run_script("generate_cluster_prompts.py")
        if success:
            st.success("Prompts generated successfully!")

    # Display prompt results if they exist
    with st.spinner("Loading prompt results..."):
        prompts = load_json_if_exists("results/prompt_results/cluster_prompts.json")

    if prompts:
        st.subheader("Generated Prompts")

        for cluster_id, cluster_data in prompts.items():
            with st.expander(
                f"{cluster_id.replace('_', ' ').title()} ({cluster_data['size']} images): {cluster_data['name']}"
            ):
                st.write("**Prompt:**")
                st.write(f"Cluster Name: {cluster_data['name']}")
                st.write(cluster_data["prompt"])

                # Display sample images from this cluster if available
                with st.spinner(
                    f"Loading sample images for {cluster_id.replace('_', ' ').title()}..."
                ):
                    cluster_results = load_json_if_exists(
                        "results/cluster_results/cluster_analysis_results.json"
                    )
                    if (
                        cluster_results
                        and cluster_id.replace("cluster_", "") in cluster_results
                    ):
                        cluster_info = cluster_results[
                            cluster_id.replace("cluster_", "")
                        ]
                        if (
                            "sample_paths" in cluster_info
                            and cluster_info["sample_paths"]
                        ):
                            st.write("**Sample Images from this Cluster:**")
                            cols = st.columns(min(3, len(cluster_info["sample_paths"])))
                            for i, img_path in enumerate(cluster_info["sample_paths"]):
                                # Check if the image exists in processed images folder
                                try:
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
                                except Exception as e:
                                    if i < len(cols):
                                        cols[i].error(
                                            f"Error processing image path: {str(e)}"
                                        )

        # Navigation suggestion
        st.info(
            "Now that you have generated prompts, you can move on to the 'Urban Design Generator' page in the sidebar."
        )
