import glob
import os
import tempfile
from typing import List

from facefusion import state_manager
from facefusion.filesystem import create_directory, move_file, remove_directory


def get_temp_file_path(file_path : str) -> str:
	_, temp_file_extension = os.path.splitext(os.path.basename(file_path))
	temp_directory_path = get_temp_directory_path(file_path)
	return os.path.join(temp_directory_path, 'temp' + temp_file_extension)


def move_temp_file(file_path : str, move_path : str) -> bool:
	temp_file_path = get_temp_file_path(file_path)
	return move_file(temp_file_path, move_path)


def get_temp_frame_paths(target_path : str) -> List[str]:
	temp_frames_pattern = get_temp_frames_pattern(target_path, '*')
	return sorted(glob.glob(temp_frames_pattern))


def get_temp_frames_pattern(target_path : str, temp_frame_prefix : str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, temp_frame_prefix + '.' + state_manager.get_item('temp_frame_format'))


def get_base_directory_path() -> str:
	return os.path.join(tempfile.gettempdir(), 'facefusion')


def create_base_directory() -> bool:
	base_directory_path = get_base_directory_path()
	return create_directory(base_directory_path)


def clear_base_directory() -> bool:
	base_directory_path = get_base_directory_path()
	return remove_directory(base_directory_path)


def get_temp_directory_path(file_path : str) -> str:
	temp_file_name, _ = os.path.splitext(os.path.basename(file_path))
	base_directory_path = get_base_directory_path()
	return os.path.join(base_directory_path, temp_file_name)


def create_temp_directory(file_path : str) -> bool:
	temp_directory_path = get_temp_directory_path(file_path)
	return create_directory(temp_directory_path)


def clear_temp_directory(file_path : str) -> bool:
	if not state_manager.get_item('keep_temp'):
		temp_directory_path = get_temp_directory_path(file_path)
		return remove_directory(temp_directory_path)
	return True
