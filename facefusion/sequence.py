import json
import os
from filesystem import create_temp, clear_temp, list_directory, is_image

def generate_sequence_json(target_folder, images_with_parameters):
    """
    Generates a JSON file with detailed configuration for each image, including 
    various parameters for processing.
    
    :param target_folder: The folder where the images are located.
    :param images_with_parameters: A list of dictionaries, each containing filename and detailed parameters.
    """
    sequence_data = {
        "target_folder": target_folder,
        "images": images_with_parameters
    }

    sequence_file_path = os.path.join(target_folder, 'sequence.json')
    with open(sequence_file_path, 'w') as json_file:
        json.dump(sequence_data, json_file, indent=4)

def generate_sequence(target_folder):
    """
    Prepares and generates a detailed sequence for processing by listing images in the target_folder,
    applying a comprehensive set of parameters for each, and generating a sequence.json file.
    
    :param target_folder: Target folder containing images for processing.
    """
    # Prepare the temporary directory
    create_temp(target_folder)

    # List all files in the target folder
    all_files = list_directory(target_folder)
    if all_files is None:
        print("Invalid directory path.")
        return

    # Filter for image files
    image_files = [file for file in all_files if is_image(os.path.join(target_folder, file))]

    # Example parameters for each image (extend or modify as needed)
    default_parameters = {
        "video_memory_strategy": "strict",
        "face_analyser_order": "left-right",
        "face_analyser_age": "adult",
        "face_analyser_gender": "female",
        "face_detector_model": "retinaface",
        "face_mask_type": "region",
        "face_mask_region": "nose",
        "temp_frame_format": "jpg",
        "output_video_encoder": "libx264",
        "output_video_preset": "medium",
        "video_template_size": 1080,
        "execution_thread_count": 4,
        "execution_queue_count": 2,
        "system_memory_limit": 32,
        "face_detector_score": 0.5,
        "face_mask_blur": 0.1,
        "face_mask_padding": 10,
        "reference_face_distance": 0.6,
        "temp_frame_quality": 90,
        "output_image_quality": 95,
        "output_video_quality": 90
    }

    images_with_parameters = [
        {"filename": image_file, "parameters": default_parameters} for image_file in image_files
    ]

    # Generate sequence.json with the image data and detailed parameters
    generate_sequence_json(target_folder, images_with_parameters)

def clear_temp_directory(target_folder):
    """
    Clears the temporary directory associated with the target_folder.
    
    :param target_folder: Target folder to clear temporary files for.
    """
    clear_temp(target_folder)

def main():
    """
    Main function to execute the sequence generation logic.
    """
    target_folder = 'img_swaps'  # Example path, replace with actual path as needed

    # Generate the sequence for processing
    generate_sequence(target_folder)
    
    # Optionally, clear the temporary directory after processing
    # clear_temp_directory(target_folder)
    
    print("Sequence generation complete.")

if __name__ == '__main__':
    main()
