import os
import zlib
from typing import Optional

from facefusion.filesystem import get_file_name, is_file


def create_hash(content : bytes, sample_size : int = 0) -> str:
	if sample_size > 0:
		sample_step = max(1, len(content) // sample_size)
		return format(zlib.crc32(content[::sample_step]), '08x')

	return format(zlib.crc32(content), '08x')


def validate_hash(validate_path : str, sample_size : int = 0) -> bool:
	hash_path = get_hash_path(validate_path)

	if is_file(hash_path):
		with open(hash_path) as hash_file:
			hash_content = hash_file.read()

		with open(validate_path, 'rb') as validate_file:
			validate_content = validate_file.read()

		return create_hash(validate_content, sample_size) == hash_content
	return False


def get_hash_path(validate_path : str) -> Optional[str]:
	if is_file(validate_path):
		validate_directory_path, file_name_and_extension = os.path.split(validate_path)
		validate_file_name = get_file_name(file_name_and_extension)

		return os.path.join(validate_directory_path, validate_file_name + '.hash')
	return None
