<<<<<<< HEAD
from typing import List, Optional
import glob
import os
import shutil
import tempfile
import filetype
from pathlib import Path

import facefusion.globals
from facefusion.common_helper import is_windows
=======
import glob
import os
import shutil
from pathlib import Path
from typing import List, Optional

import filetype

from facefusion.common_helper import is_windows
from facefusion.typing import File
>>>>>>> origin/master

if is_windows():
	import ctypes


<<<<<<< HEAD
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


=======
>>>>>>> origin/master
def get_file_size(file_path : str) -> int:
	if is_file(file_path):
		return os.path.getsize(file_path)
	return 0


<<<<<<< HEAD
=======
def same_file_extension(file_paths : List[str]) -> bool:
	file_extensions : List[str] = []

	for file_path in file_paths:
		_, file_extension = os.path.splitext(file_path.lower())

		if file_extensions and file_extension not in file_extensions:
			return False
		file_extensions.append(file_extension)
	return True


>>>>>>> origin/master
def is_file(file_path : str) -> bool:
	return bool(file_path and os.path.isfile(file_path))


def is_directory(directory_path : str) -> bool:
	return bool(directory_path and os.path.isdir(directory_path))


<<<<<<< HEAD
=======
def in_directory(file_path : str) -> bool:
	if file_path and not is_directory(file_path):
		return is_directory(os.path.dirname(file_path))
	return False


>>>>>>> origin/master
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


<<<<<<< HEAD
def list_directory(directory_path : str) -> Optional[List[str]]:
	if is_directory(directory_path):
		files = os.listdir(directory_path)
		files = [ Path(file).stem for file in files if not Path(file).stem.startswith(('.', '__')) ]
		return sorted(files)
	return None


=======
>>>>>>> origin/master
def sanitize_path_for_windows(full_path : str) -> Optional[str]:
	buffer_size = 0

	while True:
		unicode_buffer = ctypes.create_unicode_buffer(buffer_size)
<<<<<<< HEAD
		buffer_threshold = ctypes.windll.kernel32.GetShortPathNameW(full_path, unicode_buffer, buffer_size) #type:ignore[attr-defined]

		if buffer_size > buffer_threshold:
			return unicode_buffer.value
		if buffer_threshold == 0:
			return None
		buffer_size = buffer_threshold
=======
		buffer_limit = ctypes.windll.kernel32.GetShortPathNameW(full_path, unicode_buffer, buffer_size) #type:ignore[attr-defined]

		if buffer_size > buffer_limit:
			return unicode_buffer.value
		if buffer_limit == 0:
			return None
		buffer_size = buffer_limit


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


def create_directory(directory_path : str) -> bool:
	if directory_path and not is_file(directory_path):
		Path(directory_path).mkdir(parents = True, exist_ok = True)
		return is_directory(directory_path)
	return False


def list_directory(directory_path : str) -> Optional[List[File]]:
	if is_directory(directory_path):
		file_paths = sorted(os.listdir(directory_path))
		files: List[File] = []

		for file_path in file_paths:
			file_name, file_extension = os.path.splitext(file_path)

			if not file_name.startswith(('.', '__')):
				files.append(
				{
					'name': file_name,
					'extension': file_extension,
					'path': os.path.join(directory_path, file_path)
				})

		return files
	return None


def resolve_file_pattern(file_pattern : str) -> List[str]:
	if in_directory(file_pattern):
		return sorted(glob.glob(file_pattern))
	return []


def remove_directory(directory_path : str) -> bool:
	if is_directory(directory_path):
		shutil.rmtree(directory_path, ignore_errors = True)
		return not is_directory(directory_path)
	return False
>>>>>>> origin/master
