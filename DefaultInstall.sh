#!/bin/bash

# Update system and install dependencies
sudo apt-get update
sudo apt-get install ffmpeg -y
sudo apt-get install mesa-va-drivers -y

# Initialize Conda if not already initialized (for first-time setup)
# This ensures Conda works in the shell session
if ! grep -q "conda initialize" "$HOME/.bashrc"; then
    conda init --all
    source "$HOME/.bashrc"
fi

# Create and activate Conda environment
conda create --name facefusion python=3.12 -y
conda activate facefusion

# Install necessary dependencies
python install.py --onnxruntime default

# Deactivate the environment
conda deactivate

# Reactivate Conda environment for subsequent steps
conda activate facefusion
