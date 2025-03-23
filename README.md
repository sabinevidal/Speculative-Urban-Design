# Urban Design Image Analysis Tool

A Streamlit-based application that processes, analyzes and clusters urban design imagery, then generates prompts for Stable Diffusion img2img transformations. Now featuring an Urban Design Generator that creates design concepts from Google Maps Street View images.

## Features

- Process images from movie-based sample folders
- Analyze urban design imagery using OpenAI GPT-4o
- Cluster similar images based on architectural style, color palette, and futuristic elements
- Generate Stable Diffusion prompts based on cluster characteristics
- Generate urban design concepts from Google Maps Street View images using Stability AI's API
- Find random urban locations or search for specific places to reimagine

## Setup

1. Clone this repository
2. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   STABILITY_API_KEY=your_stability_api_key_here
   RAPIDAPI_KEY=your_rapidapi_key_here
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```
3. Create and activate a conda environment:

   **Option 1: Using environment.yml (recommended)**
   ```
   conda env create -f environment.yml
   conda activate img_env
   ```

   **Option 2: Manual installation**
   ```
   conda create -n img_env python=3.8
   conda activate img_env
   conda install -c conda-forge streamlit openai scikit-learn matplotlib seaborn pillow python-dotenv numpy requests
   ```

## API Keys

To use all features of this application, you'll need to obtain the following API keys:

- **OpenAI API Key**: Used for image analysis with GPT-4o. [Get key here](https://platform.openai.com/api-keys)
- **Stability AI API Key**: Required for image-to-image transformations. [Sign up here](https://platform.stability.ai/docs/getting-started/authentication)
- **RapidAPI Key**: Used to access Google Maps Geocoding API. [Sign up on RapidAPI](https://rapidapi.com/signup)
- **Google Maps API Key**: Used for Street View images. [Get key from Google Cloud Console](https://console.cloud.google.com/google/maps-apis/start)

## Running the Application

Activate the conda environment and run the Streamlit app:

```
conda activate img_env
streamlit run app.py
```

To test the Urban Design Generator functionality directly (without the Streamlit UI):

```
python demo_urban_design.py --random  # Test with a random location
python demo_urban_design.py --location "Times Square, New York"  # Test with a specific location
```

## Workflow

The application follows a simple workflow:

1. **Image Processing & Analysis**:
   - Browse sample movie-themed urban design images
   - Process images with OpenAI GPT-4o for analysis
   - Run cluster analysis to group similar images

2. **Prompt Generation**:
   - Generate Stable Diffusion img2img prompts based on each cluster's characteristics

3. **Urban Design Generator**:
   - Choose between random urban locations or specific places
   - Retrieve Street View images using Google Maps API
   - Transform these images into urban design concepts using Stability AI
   - View the original and transformed images side by side

## Project Structure

- `app.py` - The Streamlit frontend application
- `image_processor.py` - Processes images and analyzes them with OpenAI
- `cluster_analysis.py` - Clusters processed images based on analysis
- `generate_cluster_prompts.py` - Creates prompts based on cluster analysis results
- `google_maps_api.py` - Handles Google Maps API interactions for finding places and retrieving Street View images
- `stability_api.py` - Interfaces with Stability AI for image transformations
- `urban_design_generator.py` - Combines Google Maps and Stability AI to generate urban design concepts
- `demo_urban_design.py` - CLI tool to test urban design generation functionality
- `sample_images/` - Contains folders of sample images by movie theme
- `processed_images/` - Stores processed images and analysis results
- `results/cluster_results/` - Stores clustering results
- `results/prompt_results/` - Stores generated prompts
- `results/urban_design/` - Stores urban design generation results

## Requirements

- Python 3.8+
- OpenAI API key
- Stability AI API key
- RapidAPI key (for Google Maps Geocoding)
- Google Maps API key
- Conda environment with dependencies installed
