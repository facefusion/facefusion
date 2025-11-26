import os
from typing import List

from facefusion.filesystem import create_directory, get_file_extension, get_file_name, move_file, remove_directory, resolve_file_pattern


def get_temp_file_path(temp_path : str, output_path : str) -> str:
	temp_directory_path = get_temp_directory_path(temp_path, output_path)
	temp_file_extension = get_file_extension(output_path)
	return os.path.join(temp_directory_path, 'temp' + temp_file_extension)


def move_temp_file(temp_path : str, output_path : str) -> bool:
	temp_file_path = get_temp_file_path(temp_path, output_path)
	return move_file(temp_file_path, output_path)


def resolve_temp_frame_paths(temp_path : str, output_path : str, temp_frame_format : str) -> List[str]:
	temp_frames_pattern = get_temp_frames_pattern(temp_path, output_path, temp_frame_format, '*')
	return resolve_file_pattern(temp_frames_pattern)


def get_temp_frames_pattern(temp_path : str, output_path : str, temp_frame_format : str, temp_frame_prefix : str) -> str:
	temp_directory_path = get_temp_directory_path(temp_path, output_path)
	return os.path.join(temp_directory_path, temp_frame_prefix + '.' + temp_frame_format)


def get_temp_directory_path(temp_path : str, output_path : str) -> str:
	temp_file_name = get_file_name(output_path)
	return os.path.join(temp_path, 'facefusion', temp_file_name)


def create_temp_directory(temp_path : str, output_path : str) -> bool:
	temp_directory_path = get_temp_directory_path(temp_path, output_path)
	return create_directory(temp_directory_path)


def clear_temp_directory(temp_path : str, output_path : str) -> bool:
	temp_directory_path = get_temp_directory_path(temp_path, output_path)
	return remove_directory(temp_directory_path)
