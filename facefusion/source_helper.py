import os
import zlib
from typing import List, Optional

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.filesystem import is_file
from facefusion.typing import DownloadSet


def has_hashes(hash_paths : List[str]) -> bool:
	return all(is_file(hash_path) for hash_path in hash_paths)


def has_sources(source_paths : List[str]) -> bool:
	return all(validate_hash(source_path) for source_path in source_paths)


def conditional_download_hashes(download_directory_path : str, hashes : DownloadSet) -> bool:
	hash_urls = [ hashes.get(hash_key).get('url') for hash_key in hashes.keys() ]
	hash_paths = [ hashes.get(hash_key).get('path') for hash_key in hashes.keys() ]

	if not has_hashes(hash_paths) and not state_manager.get_item('skip_download'):
		process_manager.check()
		conditional_download(download_directory_path, hash_urls)
		process_manager.end()
	return has_hashes(hash_paths)


def conditional_download_sources(download_directory_path : str, sources : DownloadSet) -> bool:
	source_urls = [ sources.get(source_key).get('url') for source_key in sources.keys() ]
	source_paths = [ sources.get(source_key).get('path') for source_key in sources.keys() ]

	if not has_sources(source_paths) and not state_manager.get_item('skip_download'):
		process_manager.check()
		conditional_download(download_directory_path, source_urls)
		process_manager.end()
	return has_sources(source_paths)


def validate_hash(validate_path : str) -> bool:
	hash_path = get_hash_path(validate_path)

	if is_file(hash_path):
		with open(hash_path, 'r') as hash_file:
			hash_content = hash_file.read().strip()

		with open(validate_path, 'rb') as validate_file:
			validate_content = validate_file.read()

		return format(zlib.crc32(validate_content), '08x') == hash_content
	return False


def get_hash_path(validate_path : str) -> Optional[str]:
	if is_file(validate_path):
		validate_directory_path, _ = os.path.split(validate_path)
		validate_file_name, _ = os.path.splitext(_)

		return os.path.join(validate_directory_path, validate_file_name + '.hash')
	return None
