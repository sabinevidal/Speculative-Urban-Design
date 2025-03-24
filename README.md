# Speculative Urban Future Generator

A Streamlit-based application that processes, analyzes and clusters urban design imagery from selected films, then generates prompts for Stable Diffusion img2img transformations. Features a Speculative Urban Future Generator that creates design concepts from street view images.

## Features

- Process and analyze urban design imagery using OpenAI GPT-4o
- Cluster similar images based on architectural style, color palette, and design elements
- Generate Stable Diffusion prompts based on cluster characteristics
- Generate urban design concepts from street view images using Stability AI's API
- Browse and explore previously generated urban designs in a gallery view

## Setup

1. Clone this repository
2. Create a `.env` file in the project root with your API keys (see `.env.example`):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   STABILITY_API_KEY=your_stability_api_key_here
   ```

3. Install dependencies:

   **Option 1: Using requirements.txt**
   ```
   pip install -r requirements.txt
   ```

   **Option 2: Using environment.yml (conda)**
   ```
   conda env create -f environment.yml
   conda activate img_env
   ```

   **Option 3: Using the setup script (on macOS/Linux)**
   ```
   ./setup_and_run.sh
   ```

## API Keys

To use all features of this application, you'll need to obtain the following API keys:

- **OpenAI API Key**: Used for image analysis with GPT-4o. [Get key here](https://platform.openai.com/api-keys)
- **Stability AI API Key**: Required for image-to-image transformations. [Sign up here](https://platform.stability.ai/docs/getting-started/authentication)
- **Google Maps API Key**: Used for Street View images. [Get key from Google Cloud Console](https://console.cloud.google.com/google/maps-apis/start)

## Running the Application

Run the Streamlit app:

```
streamlit run Home.py
```

Or use the convenience script:

```
./run_app.sh
```

## Application Workflow

The application is structured as a multi-page Streamlit app with the following sections:

1. **Home**: Overview and recent results display

2. **Image Processing & Analysis**:
   - Browse and select urban design images
   - Process images with OpenAI GPT-4o for detailed analysis
   - Run cluster analysis to group similar images

3. **Generate Prompts**:
   - Generate Stable Diffusion img2img prompts based on each cluster's characteristics
   - View and edit generated prompts

4. **Speculative Urban Future Generator**:
   - Select street view images from the library
   - Choose design concept prompts
   - Transform street views into speculative urban future concepts using Stability AI
   - Adjust transformation parameters

5. **Speculative Urban Future Gallery**:
   - Browse previously generated urban futures
   - View original and transformed images side by side
   - Explore design concepts with their associated metadata

## Project Structure

- `Home.py` - The main Streamlit application
- `pages/` - Contains the individual pages of the Streamlit application
  - `1_Image_Processing_Analysis.py` - Image processing and analysis page
  - `2_Generate_Prompts.py` - Prompt generation page
  - `3_Urban_Future_Generator.py` - Speculative urban future generator page
  - `4_Urban_Future_Gallery.py` - Speculative urban future gallery page
- `image_processor.py` - Processes images and analyzes them with OpenAI
- `cluster_analysis.py` - Clusters processed images based on analysis
- `google_maps_api.py` - Handles Google Maps API interactions for Street View images
- `stability_api.py` - Interfaces with Stability AI for image transformations
- `urban_future_generator.py` - Combines image processing and Stability AI to generate speculative urban future concepts
- `sample_images/` - Contains sample urban design images
- `streetview_images/` - Stores street view images used for transformation
- `processed_images/` - Stores processed images and analysis results
- `results/` - Stores clustering results, prompts, and generated urban future outputs

## Requirements

- Python 3.8+
- OpenAI API key
- Stability AI API key
- Google Maps API key
- Streamlit and other dependencies as listed in requirements.txt
