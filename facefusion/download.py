import os
import shutil
import subprocess
from functools import lru_cache
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from tqdm import tqdm

import facefusion.choices
from facefusion import logger, process_manager, state_manager, wording
from facefusion.filesystem import get_file_size, is_file, remove_file
from facefusion.hash_helper import validate_hash
from facefusion.typing import DownloadProvider, DownloadSet


def open_curl(args : List[str]) -> subprocess.Popen[bytes]:
	commands = [ shutil.which('curl'), '--silent', '--insecure', '--location' ]
	commands.extend(args)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def conditional_download(download_directory_path : str, urls : List[str]) -> None:
	for url in urls:
		download_file_name = os.path.basename(urlparse(url).path)
		download_file_path = os.path.join(download_directory_path, download_file_name)
		initial_size = get_file_size(download_file_path)
		download_size = get_static_download_size(url)

		if initial_size < download_size:
			with tqdm(total = download_size, initial = initial_size, desc = wording.get('downloading'), unit = 'B', unit_scale = True, unit_divisor = 1024, ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
				commands = [ '--create-dirs', '--continue-at', '-', '--output', download_file_path, url ]
				open_curl(commands)
				current_size = initial_size
				progress.set_postfix(download_providers = state_manager.get_item('download_providers'), file_name = download_file_name)

				while current_size < download_size:
					if is_file(download_file_path):
						current_size = get_file_size(download_file_path)
						progress.update(current_size - progress.n)


@lru_cache(maxsize = None)
def get_static_download_size(url : str) -> int:
	commands = [ '-I', url ]
	process = open_curl(commands)
	lines = reversed(process.stdout.readlines())

	for line in lines:
		__line__ = line.decode().lower()
		if 'content-length:' in __line__:
			_, content_length = __line__.split('content-length:')
			return int(content_length)

	return 0


@lru_cache(maxsize = None)
def ping_static_url(url : str) -> bool:
	commands = [ '-I', url ]
	process = open_curl(commands)
	process.communicate()
	return process.returncode == 0


def conditional_download_hashes(hashes : DownloadSet) -> bool:
	hash_paths = [ hashes.get(hash_key).get('path') for hash_key in hashes.keys() ]

	process_manager.check()
	_, invalid_hash_paths = validate_hash_paths(hash_paths)
	if invalid_hash_paths:
		for index in hashes:
			if hashes.get(index).get('path') in invalid_hash_paths:
				invalid_hash_url = hashes.get(index).get('url')
				if invalid_hash_url:
					download_directory_path = os.path.dirname(hashes.get(index).get('path'))
					conditional_download(download_directory_path, [ invalid_hash_url ])

	valid_hash_paths, invalid_hash_paths = validate_hash_paths(hash_paths)

	for valid_hash_path in valid_hash_paths:
		valid_hash_file_name, _ = os.path.splitext(os.path.basename(valid_hash_path))
		logger.debug(wording.get('validating_hash_succeed').format(hash_file_name = valid_hash_file_name), __name__)
	for invalid_hash_path in invalid_hash_paths:
		invalid_hash_file_name, _ = os.path.splitext(os.path.basename(invalid_hash_path))
		logger.error(wording.get('validating_hash_failed').format(hash_file_name = invalid_hash_file_name), __name__)

	if not invalid_hash_paths:
		process_manager.end()
	return not invalid_hash_paths


def conditional_download_sources(sources : DownloadSet) -> bool:
	source_paths = [ sources.get(source_key).get('path') for source_key in sources.keys() ]

	process_manager.check()
	_, invalid_source_paths = validate_source_paths(source_paths)
	if invalid_source_paths:
		for index in sources:
			if sources.get(index).get('path') in invalid_source_paths:
				invalid_source_url = sources.get(index).get('url')
				if invalid_source_url:
					download_directory_path = os.path.dirname(sources.get(index).get('path'))
					conditional_download(download_directory_path, [ invalid_source_url ])

	valid_source_paths, invalid_source_paths = validate_source_paths(source_paths)

	for valid_source_path in valid_source_paths:
		valid_source_file_name, _ = os.path.splitext(os.path.basename(valid_source_path))
		logger.debug(wording.get('validating_source_succeed').format(source_file_name = valid_source_file_name), __name__)
	for invalid_source_path in invalid_source_paths:
		invalid_source_file_name, _ = os.path.splitext(os.path.basename(invalid_source_path))
		logger.error(wording.get('validating_source_failed').format(source_file_name = invalid_source_file_name), __name__)

		if remove_file(invalid_source_path):
			logger.error(wording.get('deleting_corrupt_source').format(source_file_name = invalid_source_file_name), __name__)

	if not invalid_source_paths:
		process_manager.end()
	return not invalid_source_paths


def validate_hash_paths(hash_paths : List[str]) -> Tuple[List[str], List[str]]:
	valid_hash_paths = []
	invalid_hash_paths = []

	for hash_path in hash_paths:
		if is_file(hash_path):
			valid_hash_paths.append(hash_path)
		else:
			invalid_hash_paths.append(hash_path)
	return valid_hash_paths, invalid_hash_paths


def validate_source_paths(source_paths : List[str]) -> Tuple[List[str], List[str]]:
	valid_source_paths = []
	invalid_source_paths = []

	for source_path in source_paths:
		if validate_hash(source_path):
			valid_source_paths.append(source_path)
		else:
			invalid_source_paths.append(source_path)
	return valid_source_paths, invalid_source_paths


def resolve_download_url(base_name : str, file_name : str) -> Optional[str]:
	download_providers = state_manager.get_item('download_providers')

	for download_provider in download_providers:
		if ping_download_provider(download_provider):
			return resolve_download_url_by_provider(download_provider, base_name, file_name)
	return None


def ping_download_provider(download_provider : DownloadProvider) -> bool:
	download_provider_value = facefusion.choices.download_provider_set.get(download_provider)
	return ping_static_url(download_provider_value.get('url'))


def resolve_download_url_by_provider(download_provider : DownloadProvider, base_name : str, file_name : str) -> Optional[str]:
	download_provider_value = facefusion.choices.download_provider_set.get(download_provider)
	return download_provider_value.get('url') + download_provider_value.get('path').format(base_name = base_name, file_name = file_name)
