import hashlib
import os
from typing import Optional

from facefusion import state_manager
from facefusion.filesystem import get_file_extension, is_image, is_video


def convert_int_none(value : int) -> Optional[int]:
	if value == 'none':
		return None
	return value


def convert_str_none(value : str) -> Optional[str]:
	if value == 'none':
		return None
	return value


def suggest_output_path(output_directory_path : str, target_path : str) -> Optional[str]:
	if is_image(target_path) or is_video(target_path):
		output_file_name = hashlib.sha1(str(state_manager.get_state()).encode()).hexdigest()[:8]
		target_file_extension = get_file_extension(target_path)
		return os.path.join(output_directory_path, output_file_name + target_file_extension)
	return None
