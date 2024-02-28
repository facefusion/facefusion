import json
import os
from filesystem import (
    create_temp, 
    clear_temp, 
    list_directory, 
    is_image
)
import numpy as np

def generate_sequence_json(target_folder, images_with_parameters):
    sequence_data = {
        "target_folder": target_folder,
        "images": images_with_parameters
    }

    sequence_file_path = os.path.join(target_folder, 'sequence.json')
    with open(sequence_file_path, 'w') as json_file:
        json.dump(sequence_data, json_file, indent=4)

def generate_sequence(target_folder, parameters={}):
    # Prepare the temporary directory
    create_temp(target_folder)

    # List all files in the target folder
    all_files = list_directory(target_folder)
    if all_files is None:
        print("Invalid directory path.")
        return

    # Filter for image files
    image_files = [file for file in all_files if is_image(os.path.join(target_folder, file))]
    
    # Assume parameters are provided; otherwise, use default parameters
    images_with_parameters = [
        {
            "filename": image_file,
            "parameters": parameters  # Example: Default or specific parameters for each image
        }
        for image_file in image_files
    ]

    # Generate sequence.json with the validated images and parameters
    generate_sequence_json(target_folder, images_with_parameters)

def clear_temp_directory(target_folder):
    clear_temp(target_folder)

# Example usage
if __name__ == '__main__':
    target_folder = 'path/to/img_swaps'
    # Example parameters - adjust as needed based on actual parameters and choices.py
    parameters = {
        "model": "default",
        "quality": "high"
    }
    generate_sequence(target_folder, parameters)
    # Optionally, clear temp directory after operation
    # clear_temp_directory(target_folder)
