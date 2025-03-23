import streamlit as st
import os
import json
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
import time
from typing import Dict

# Load environment variables from .env file
load_dotenv()

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
                    st.error(f"Error loading JSON file {file_path}: {e}")
                    return []
        except Exception as e:
            st.error(f"Error reading file {file_path}: {e}")
            return []
    return None


def verify_openai_api_key():
    """Verify that the OpenAI API key is valid."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not found. Please add it to your .env file.")
        return None

    # A simple check to see if the key is properly formatted
    if not api_key.startswith(("sk-", "OPENAI-")):
        st.warning("Your OpenAI API key doesn't seem to have the expected format.")

    return api_key


def create_cluster_summary(cluster_data: Dict) -> str:
    """Create a summary of cluster characteristics for prompt generation."""
    summary = []

    if cluster_data.get("common_labels"):
        summary.append("Common Labels: " + ", ".join(cluster_data["common_labels"]))

    if cluster_data.get("common_styles"):
        summary.append("Styles: " + ", ".join(cluster_data["common_styles"]))

    if cluster_data.get("common_elements"):
        summary.append("Key Elements: " + ", ".join(cluster_data["common_elements"]))

    if cluster_data.get("common_materials"):
        summary.append("Materials: " + ", ".join(cluster_data["common_materials"]))

    if cluster_data.get("common_moods"):
        summary.append("Moods: " + ", ".join(cluster_data["common_moods"]))

    if cluster_data.get("common_colors"):
        summary.append("Colors: " + ", ".join(cluster_data["common_colors"]))

    return "\n".join(summary)


def generate_prompt(client: OpenAI, cluster_summary: str) -> Dict:
    """Generate a Stable Diffusion img2img prompt using OpenAI."""
    system_prompt = """You are an expert at creating prompts for Stable Diffusion img2img.
    Based on the cluster analysis of urban design images provided, create a detailed prompt that captures the essence
    of the cluster's aesthetic and can be used to transform real urban photographs.
    Focus on architectural elements, mood, lighting, and style. The prompt should be detailed but concise. Come up with a name for the cluster."""

    user_prompt = f"""Based on this cluster analysis of urban design images, create a Stable Diffusion img2img prompt:

    {cluster_summary}

    Create a prompt that will help transform a real urban photograph to match this aesthetic."""

    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=user_prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "cluster_prompts",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the cluster",
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The Stable Diffusion img2img prompt",
                            },
                        },
                        "required": ["name", "prompt"],
                        "additionalProperties": False,
                    },
                },
            },
        )

        # Parse the JSON response
        try:
            response_data = json.loads(response.output_text)
            return response_data
        except json.JSONDecodeError:
            st.error(f"Error parsing OpenAI response: {response.output_text}")
            return {"name": "Parsing Error", "prompt": "Error generating prompt"}
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return {"name": "API Error", "prompt": f"Error generating prompt: {str(e)}"}


def generate_cluster_prompts():
    """Generate prompts for all clusters using OpenAI API"""
    # Verify API key
    api_key = verify_openai_api_key()
    if not api_key:
        return False

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Load cluster data
    cluster_data = load_json_if_exists(
        "results/cluster_results/cluster_analysis_results.json"
    )
    if not cluster_data:
        st.error("No cluster analysis results found.")
        return False

    # Create output directory if it doesn't exist
    os.makedirs("results/prompt_results", exist_ok=True)

    # Generate and save prompts for each cluster
    prompts = {}
    total_clusters = len(cluster_data)

    # Setup progress tracking
    progress_text = st.empty()
    progress_text.text(f"Found {total_clusters} clusters to process")
    progress_bar = st.progress(0)

    for i, (cluster_id, cluster_info) in enumerate(cluster_data.items()):
        # Update progress
        progress_text.text(
            f"Generating prompt for cluster {cluster_id} ({i+1}/{total_clusters})..."
        )
        progress = (i) / total_clusters
        progress_bar.progress(progress)

        # Generate prompt
        cluster_summary = create_cluster_summary(cluster_info)
        prompt_data = generate_prompt(client, cluster_summary)

        # Store result
        prompts[f"cluster_{cluster_id}"] = {
            "size": cluster_info["size"],
            "name": prompt_data["name"],
            "prompt": prompt_data["prompt"],
        }

        # Small delay to prevent rate limiting
        time.sleep(0.1)

    # Complete progress bar
    progress_bar.progress(1.0)
    progress_text.text("Prompt generation completed!")

    # Save prompts to file
    output_path = "results/prompt_results/cluster_prompts.json"
    try:
        with open(output_path, "w") as f:
            json.dump(prompts, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving prompts to file: {str(e)}")
        return False


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
        with st.spinner("Generating prompts..."):
            success = generate_cluster_prompts()
            if success:
                st.success("Prompts generated successfully!")
                st.rerun()  # Rerun to refresh and display the results

    # Display prompt results if they exist
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
                                if i < len(cols):  # Ensure we stay within column bounds
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
                                        elif error:
                                            cols[i].error(error)
                                    except Exception as e:
                                        cols[i].error(
                                            f"Error processing image: {str(e)}"
                                        )

        # Navigation suggestion
        st.info(
            "Now that you have generated prompts, you can move on to the 'Urban Design Generator' page in the sidebar."
        )
