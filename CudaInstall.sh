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
conda install conda-forge::cuda-runtime=12.4.1 conda-forge::cudnn=9.2.1.18 -y
pip install tensorrt==10.6.0 --extra-index-url https://pypi.nvidia.com

# Deactivate the environment (if you need to switch or finish setup)
conda deactivate

# Reactivate Conda environment for subsequent steps
conda activate facefusion
