import glob
import os
import shutil
from typing import List, Optional

import facefusion.choices


def get_file_size(file_path : str) -> int:
	if is_file(file_path):
		return os.path.getsize(file_path)
	return 0


def get_file_name(file_path : str) -> Optional[str]:
	file_name, _ = os.path.splitext(os.path.basename(file_path))

	if file_name:
		return file_name
	return None


def get_file_extension(file_path : str) -> Optional[str]:
	_, file_extension = os.path.splitext(file_path)

	if file_extension:
		return file_extension.lower()
	return None


def get_file_format(file_path : str) -> Optional[str]:
	file_extension = get_file_extension(file_path)

	if file_extension:
		if file_extension == '.jpg':
			return 'jpeg'
		if file_extension == '.tif':
			return 'tiff'
		return file_extension.lstrip('.')
	return None


def same_file_extension(first_file_path : str, second_file_path : str) -> bool:
	first_file_extension = get_file_extension(first_file_path)
	second_file_extension = get_file_extension(second_file_path)

	if first_file_extension and second_file_extension:
		return get_file_extension(first_file_path) == get_file_extension(second_file_path)
	return False


def is_file(file_path : str) -> bool:
	if file_path:
		return os.path.isfile(file_path)
	return False


def is_audio(audio_path : str) -> bool:
	return is_file(audio_path) and get_file_format(audio_path) in facefusion.choices.audio_formats


def has_audio(audio_paths : List[str]) -> bool:
	if audio_paths:
		return any(map(is_audio, audio_paths))
	return False


def are_audios(audio_paths : List[str]) -> bool:
	if audio_paths:
		return all(map(is_audio, audio_paths))
	return False


def is_image(image_path : str) -> bool:
	return is_file(image_path) and get_file_format(image_path) in facefusion.choices.image_formats


def has_image(image_paths : List[str]) -> bool:
	if image_paths:
		return any(is_image(image_path) for image_path in image_paths)
	return False


def are_images(image_paths : List[str]) -> bool:
	if image_paths:
		return all(map(is_image, image_paths))
	return False


def is_video(video_path : str) -> bool:
	return is_file(video_path) and get_file_format(video_path) in facefusion.choices.video_formats


def has_video(video_paths : List[str]) -> bool:
	if video_paths:
		return any(map(is_video, video_paths))
	return False


def are_videos(video_paths : List[str]) -> bool:
	if video_paths:
		return any(map(is_video, video_paths))
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
	if directory_path:
		return os.path.isdir(directory_path)
	return False


def in_directory(file_path : str) -> bool:
	if file_path:
		directory_path = os.path.dirname(file_path)
		if directory_path:
			return not is_directory(file_path) and is_directory(directory_path)
	return False


def create_directory(directory_path : str) -> bool:
	if directory_path and not is_file(directory_path):
		os.makedirs(directory_path, exist_ok = True)
		return is_directory(directory_path)
	return False


def remove_directory(directory_path : str) -> bool:
	if is_directory(directory_path):
		shutil.rmtree(directory_path, ignore_errors = True)
		return not is_directory(directory_path)
	return False


def resolve_relative_path(path : str) -> str:
	return os.path.abspath(os.path.join(os.path.dirname(__file__), path))
