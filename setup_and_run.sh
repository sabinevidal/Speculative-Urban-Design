#!/bin/bash

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install Miniconda or Anaconda."
    exit 1
fi

# Create and activate conda environment
echo "Creating conda environment 'img_env'..."
conda create -y -n img_env python=3.12
eval "$(conda shell.bash hook)"
conda activate img_env

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists, if not create it from .env.example
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env file from .env.example. Please edit it to add your OpenAI API key."
        exit 1
    else
        echo "ERROR: .env.example file not found."
        exit 1
    fi
fi

# Run the script with default parameters
echo "Running image_processor.py..."
python image_processor.py

echo "Completed! Results are in the processed_images directory."
