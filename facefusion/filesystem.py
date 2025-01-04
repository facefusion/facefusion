import glob
import os
import shutil
from pathlib import Path
from typing import List, Optional

import facefusion.choices


def get_file_size(file_path : str) -> int:
	if is_file(file_path):
		return os.path.getsize(file_path)
	return 0


def get_file_name(file_path : str) -> Optional[str]:
	if is_file(file_path):
		file_name, _ = os.path.splitext(file_path)
		return file_name
	return None


def get_file_extension(file_path : str) -> Optional[str]:
	if is_file(file_path):
		_, file_extension = os.path.splitext(file_path)
		return file_extension
	return None


def get_file_format(file_path : str) -> Optional[str]:
	if is_file(file_path):
		return get_file_extension(file_path).lower().lstrip('.')
	return None


def same_file_extension(file_paths : List[str]) -> bool:
	file_extensions : List[str] = []

	for file_path in file_paths:
		file_extension = get_file_extension(file_path)
		if file_extension and file_extension not in file_extensions:
			return False
		file_extensions.append(file_extension)

	return True


def is_file(file_path : str) -> bool:
	return bool(file_path and os.path.isfile(file_path))


def is_audio(audio_path : str) -> bool:
	if is_file(audio_path):
		return get_file_format(audio_path) in facefusion.choices.audio_formats
	return False


def has_audio(audio_paths : List[str]) -> bool:
	if audio_paths:
		return any(is_audio(audio_path) for audio_path in audio_paths)
	return False


def is_image(image_path : str) -> bool:
	if is_file(image_path):
		_, image_file_format = os.path.splitext(image_path.lower())
		return image_file_format in facefusion.choices.image_formats
	return False


def has_image(image_paths: List[str]) -> bool:
	if image_paths:
		return any(is_image(image_path) for image_path in image_paths)
	return False


def is_video(video_path : str) -> bool:
	if is_file(video_path):
		return get_file_format(video_path) in facefusion.choices.video_formats
	return False


def filter_audio_paths(paths : List[str]) -> List[str]:
	if paths:
		return [ path for path in paths if is_audio(path) ]
	return []


def filter_image_paths(paths : List[str]) -> List[str]:
	if paths:
		return [ path for path in paths if is_image(path) ]
	return []


def copy_file(file_path : str, move_path : str) -> bool:
	if is_file(file_path):
		shutil.copy(file_path, move_path)
		return is_file(move_path)
	return False


def move_file(file_path : str, move_path : str) -> bool:
	if is_file(file_path):
		shutil.move(file_path, move_path)
		return not is_file(file_path) and is_file(move_path)
	return False


def remove_file(file_path : str) -> bool:
	if is_file(file_path):
		os.remove(file_path)
		return not is_file(file_path)
	return False


def resolve_file_paths(directory_path : str) -> List[str]:
	file_paths : List[str] = []

	if is_directory(directory_path):
		file_names_and_extensions = sorted(os.listdir(directory_path))

		for file_name_and_extension in file_names_and_extensions:
			if not file_name_and_extension.startswith(('.', '__')):
				file_path = os.path.join(directory_path, file_name_and_extension)
				file_paths.append(file_path)

	return file_paths


def resolve_file_pattern(file_pattern : str) -> List[str]:
	if in_directory(file_pattern):
		return sorted(glob.glob(file_pattern))
	return []


def is_directory(directory_path : str) -> bool:
	return bool(directory_path and os.path.isdir(directory_path))


def in_directory(file_path : str) -> bool:
	if file_path and not is_directory(file_path):
		return is_directory(os.path.dirname(file_path))
	return False


def create_directory(directory_path : str) -> bool:
	if directory_path and not is_file(directory_path):
		Path(directory_path).mkdir(parents = True, exist_ok = True)
		return is_directory(directory_path)
	return False


def remove_directory(directory_path : str) -> bool:
	if is_directory(directory_path):
		shutil.rmtree(directory_path, ignore_errors = True)
		return not is_directory(directory_path)
	return False


def resolve_relative_path(path : str) -> str:
	return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
