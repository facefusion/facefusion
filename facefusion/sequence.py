import argparse
import json
import os
from filesystem import create_temp, clear_temp, list_directory, is_image

def generate_sequence_json(target_folder, parameters={}):
    # Prepare the temporary directory
    create_temp(target_folder)

    # List all files in the target folder
    all_files = list_directory(target_folder)
    if all_files is None:
        print("Invalid directory path.")
        return

    # Filter for image files
    image_files = [file for file in all_files if is_image(os.path.join(target_folder, file))]
    
    images_with_parameters = [
        {"filename": image_file, "parameters": parameters}
        for image_file in image_files
    ]

    sequence_data = {"target_folder": target_folder, "images": images_with_parameters}
    sequence_file_path = os.path.join(target_folder, 'sequence.json')
    with open(sequence_file_path, 'w') as json_file:
        json.dump(sequence_data, json_file, indent=4)

def main():
    parser = argparse.ArgumentParser(description='Generate a sequence for face swapping.')
    parser.add_argument('target_folder', type=str, help='Path to the target folder containing images.')
    parser.add_argument('--clear_temp', action='store_true', help='Clear temporary files after processing.')
    args = parser.parse_args()

    # Example: Default parameters for image processing
    parameters = {"model": "default", "quality": "high"}

    generate_sequence_json(args.target_folder, parameters)

    if args.clear_temp:
        clear_temp(args.target_folder)
        print("Temporary files cleared.")

if __name__ == '__main__':
    main()
