import shutil
from typing import List, Optional
import os
import filetype
from pathlib import Path

from facefusion.common_helper import is_windows

if is_windows():
	import ctypes


def get_file_size(file_path : str) -> int:
	if is_file(file_path):
		return os.path.getsize(file_path)
	return 0


def same_file_extension(file_paths : List[str]) -> bool:
	file_extensions : List[str] = []

	for file_path in file_paths:
		_, file_extension = os.path.splitext(file_path)

		if file_extensions and file_extension not in file_extensions:
			return False
		file_extensions.append(file_extension)
	return True


def is_file(file_path : str) -> bool:
	return bool(file_path and os.path.isfile(file_path))


def is_directory(directory_path : str) -> bool:
	return bool(directory_path and os.path.isdir(directory_path))


def in_directory(file_path : str) -> bool:
	if not is_directory(file_path):
		return is_directory(os.path.dirname(file_path))
	return False


def is_audio(audio_path : str) -> bool:
	return is_file(audio_path) and filetype.helpers.is_audio(audio_path)


def has_audio(audio_paths : List[str]) -> bool:
	if audio_paths:
		return any(is_audio(audio_path) for audio_path in audio_paths)
	return False


def is_image(image_path : str) -> bool:
	return is_file(image_path) and filetype.helpers.is_image(image_path)


def has_image(image_paths: List[str]) -> bool:
	if image_paths:
		return any(is_image(image_path) for image_path in image_paths)
	return False


def is_video(video_path : str) -> bool:
	return is_file(video_path) and filetype.helpers.is_video(video_path)


def filter_audio_paths(paths : List[str]) -> List[str]:
	if paths:
		return [ path for path in paths if is_audio(path) ]
	return []


def filter_image_paths(paths : List[str]) -> List[str]:
	if paths:
		return [ path for path in paths if is_image(path) ]
	return []


def resolve_relative_path(path : str) -> str:
	return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def list_directory(directory_path : str) -> Optional[List[str]]:
	if is_directory(directory_path):
		files = os.listdir(directory_path)
		files = [ Path(file).stem for file in files if not Path(file).stem.startswith(('.', '__')) ]
		return sorted(files)
	return None


def sanitize_path_for_windows(full_path : str) -> Optional[str]:
	buffer_size = 0

	while True:
		unicode_buffer = ctypes.create_unicode_buffer(buffer_size)
		buffer_threshold = ctypes.windll.kernel32.GetShortPathNameW(full_path, unicode_buffer, buffer_size) #type:ignore[attr-defined]

		if buffer_size > buffer_threshold:
			return unicode_buffer.value
		if buffer_threshold == 0:
			return None
		buffer_size = buffer_threshold


def move_file(file_path : str, move_path : str) -> bool:
	if is_file(file_path):
		shutil.move(file_path, move_path)
		return is_file(move_path)
	return False
