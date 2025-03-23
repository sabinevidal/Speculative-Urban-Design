import json
import os
from openai import OpenAI
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def verify_openai_api_key():
    """Verify that the OpenAI API key is valid."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. Make sure to set it in the .env file."
        )

    # A simple check to see if the key is properly formatted
    if not api_key.startswith(("sk-", "OPENAI-")):
        print("Warning: Your OpenAI API key doesn't seem to have the expected format.")

    return api_key


# Get API key from environment and verify it
OPENAI_API_KEY = verify_openai_api_key()


def load_cluster_data(file_path: str) -> Dict:
    """Load the cluster analysis results from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


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


def generate_prompt(client: OpenAI, cluster_summary: str) -> str:
    """Generate a Stable Diffusion img2img prompt using OpenAI."""
    system_prompt = """You are an expert at creating prompts for Stable Diffusion img2img.
    Based on the cluster analysis of urban design images provided, create a detailed prompt that captures the essence
    of the cluster's aesthetic and can be used to transform real urban photographs.
    Focus on architectural elements, mood, lighting, and style. The prompt should be detailed but concise. Come up with a name for the cluster."""

    user_prompt = f"""Based on this cluster analysis of urban design images, create a Stable Diffusion img2img prompt:

    {cluster_summary}

    Create a prompt that will help transform a real urban photograph to match this aesthetic."""

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
        print(f"Error parsing response: {response.output_text}")
        return {"name": "Parsing Error", "prompt": "Error generating prompt"}


def main():
    # Initialize OpenAI client with API key
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Load cluster data
    print("Loading cluster analysis results...")
    cluster_data = load_cluster_data(
        "results/cluster_results/cluster_analysis_results.json"
    )

    # Create output directory if it doesn't exist
    os.makedirs("results/prompt_results", exist_ok=True)

    # Generate and save prompts for each cluster
    prompts = {}
    total_clusters = len(cluster_data)
    print(f"Found {total_clusters} clusters to process")

    for i, (cluster_id, cluster_info) in enumerate(cluster_data.items()):
        print(f"Generating prompt for cluster {cluster_id} ({i+1}/{total_clusters})...")
        cluster_summary = create_cluster_summary(cluster_info)
        prompt_data = generate_prompt(client, cluster_summary)
        prompts[f"cluster_{cluster_id}"] = {
            "size": cluster_info["size"],
            "name": prompt_data["name"],
            "prompt": prompt_data["prompt"],
        }
        print(f"Completed prompt generation for cluster {cluster_id}")

    # Save prompts to file
    output_path = "results/prompt_results/cluster_prompts.json"
    print("Saving prompt results...")
    with open(output_path, "w") as f:
        json.dump(prompts, f, indent=2)

    print(f"Prompts have been generated and saved to {output_path}")


if __name__ == "__main__":
    main()
