from typing import List
from pathlib import Path
import glob
import os
import shutil
import tempfile

import facefusion.globals
from facefusion.filesystem import is_file, is_directory


def get_temp_frame_paths(target_path : str) -> List[str]:
	temp_frames_pattern = get_temp_frames_pattern(target_path, '*')
	return sorted(glob.glob(temp_frames_pattern))


def get_temp_frames_pattern(target_path : str, temp_frame_prefix : str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, temp_frame_prefix + '.' + facefusion.globals.temp_frame_format)


def get_temp_file_path(target_path : str) -> str:
	_, target_extension = os.path.splitext(os.path.basename(target_path))
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, 'temp' + target_extension)


def get_temp_directory_path(target_path : str) -> str:
	target_name, _ = os.path.splitext(os.path.basename(target_path))
	temp_directory_path = os.path.join(tempfile.gettempdir(), 'facefusion')
	return os.path.join(temp_directory_path, target_name)


def create_temp(target_path : str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	Path(temp_directory_path).mkdir(parents = True, exist_ok = True)


def move_temp(target_path : str, output_path : str) -> None:
	temp_file_path = get_temp_file_path(target_path)

	if is_file(temp_file_path):
		if is_file(output_path):
			os.remove(output_path)
		shutil.move(temp_file_path, output_path)


def clear_temp(target_path : str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	parent_directory_path = os.path.dirname(temp_directory_path)

	if not facefusion.globals.keep_temp and is_directory(temp_directory_path):
		shutil.rmtree(temp_directory_path, ignore_errors = True)
	if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
		os.rmdir(parent_directory_path)
