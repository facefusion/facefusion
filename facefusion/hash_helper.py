import os
import zlib
from typing import Optional

from facefusion.filesystem import is_file


def create_hash(content : bytes) -> str:
	return format(zlib.crc32(content), '08x')


def validate_hash(validate_path : str) -> bool:
	hash_path = get_hash_path(validate_path)

	if is_file(hash_path):
		with open(hash_path, 'r') as hash_file:
			hash_content = hash_file.read().strip()

		with open(validate_path, 'rb') as validate_file:
			validate_content = validate_file.read()

		return create_hash(validate_content) == hash_content
	return False


def get_hash_path(validate_path : str) -> Optional[str]:
	if is_file(validate_path):
		validate_directory_path, _ = os.path.split(validate_path)
		validate_file_name, _ = os.path.splitext(_)

		return os.path.join(validate_directory_path, validate_file_name + '.hash')
	return None
