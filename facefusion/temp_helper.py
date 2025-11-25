import os
from typing import List

from facefusion.filesystem import create_directory, get_file_extension, get_file_name, move_file, remove_directory, resolve_file_pattern


def get_temp_file_path(file_path : str, temp_path : str) -> str:
	temp_directory_path = get_temp_directory_path(file_path, temp_path)
	temp_file_extension = get_file_extension(file_path)
	return os.path.join(temp_directory_path, 'temp' + temp_file_extension)


def move_temp_file(move_path : str, temp_path : str) -> bool:
	temp_file_path = get_temp_file_path(move_path, temp_path)
	return move_file(temp_file_path, move_path)


def resolve_temp_frame_paths(target_path : str, temp_path : str, temp_frame_format : str) -> List[str]:
	temp_frames_pattern = get_temp_frames_pattern(target_path, '*', temp_path, temp_frame_format)
	return resolve_file_pattern(temp_frames_pattern)


def get_temp_frames_pattern(target_path : str, temp_frame_prefix : str, temp_path : str, temp_frame_format : str) -> str:
	temp_directory_path = get_temp_directory_path(target_path, temp_path)
	return os.path.join(temp_directory_path, temp_frame_prefix + '.' + temp_frame_format)


def get_temp_directory_path(file_path : str, temp_path : str) -> str:
	temp_file_name = get_file_name(file_path)
	return os.path.join(temp_path, 'facefusion', temp_file_name)


def create_temp_directory(file_path : str, temp_path : str) -> bool:
	temp_directory_path = get_temp_directory_path(file_path, temp_path)
	return create_directory(temp_directory_path)


def clear_temp_directory(file_path : str, temp_path : str) -> bool:
	temp_directory_path = get_temp_directory_path(file_path, temp_path)
	return remove_directory(temp_directory_path)


def get_temp_sequence_paths(file_path : str, frame_total : int, temp_frame_prefix : str, temp_frame_format : str, temp_path : str) -> List[str]:
	temp_directory_path = get_temp_directory_path(file_path, temp_path)
	temp_frame_paths = []

	for frame_number in range(frame_total):
		temp_file_name = temp_frame_prefix % (frame_number + 1) + '.' + temp_frame_format
		temp_frame_path = os.path.join(temp_directory_path, temp_file_name)
		temp_frame_paths.append(temp_frame_path)
	return temp_frame_paths
