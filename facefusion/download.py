import os
import subprocess
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

import facefusion.choices
from facefusion import cli_progress, curl_builder, logger, process_manager, state_manager, translator
from facefusion.filesystem import get_file_extension, get_file_size, is_file, remove_file
from facefusion.hash_helper import validate_hash
from facefusion.types import Buffer, Command, DownloadProvider, DownloadSet


def open_curl(commands : List[Command]) -> subprocess.Popen[Buffer]:
	commands = curl_builder.run(commands)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def conditional_download(download_directory_path : str, urls : List[str]) -> None:
	for url in urls:
		download_file_name = os.path.basename(urlparse(url).path)
		download_file_path = os.path.join(download_directory_path, download_file_name)
		initial_size = get_file_size(download_file_path)
		download_size = get_static_download_size(url)

		if initial_size < download_size:
			with cli_progress.create(unit = 'download', total = download_size) as progress:
				progress.set_title(translator.get('downloading'))
				progress.set_description('file_name = ' + download_file_name)

				commands = curl_builder.chain(
					curl_builder.download(url, download_file_path),
					curl_builder.set_timeout(5),
					curl_builder.set_retry(5)
				)
				open_curl(commands)
				current_size = initial_size

				while current_size < download_size:
					if is_file(download_file_path):
						current_size = get_file_size(download_file_path)
						progress.seek(current_size)


@lru_cache(maxsize = 64)
def get_static_download_size(url : str) -> int:
	commands = curl_builder.chain(
		curl_builder.ping(url),
		curl_builder.set_timeout(5)
	)
	process = open_curl(commands)
	lines = reversed(process.stdout.readlines())

	if process.wait() == 0:
		for line in lines:
			__line__ = line.decode().lower()

			if 'content-length:' in __line__:
				_, content_length = __line__.split('content-length:')
				return int(content_length)

	return 0


@lru_cache(maxsize = 64)
def ping_static_url(url : str) -> bool:
	commands = curl_builder.chain(
		curl_builder.ping(url),
		curl_builder.set_timeout(5)
	)
	process = open_curl(commands)
	process.communicate()
	return process.returncode == 0


def conditional_download_files(file_set : DownloadSet) -> bool:
	process_manager.check()

	for file in file_set.values():
		file_url = file.get('url')
		file_path = file.get('path')

		if not validate_file(file_path) and file_url:
			conditional_download(os.path.dirname(file_path), [ file_url ])

	is_valid = conditional_validate_files(file_set)
	process_manager.end()

	return is_valid


def conditional_validate_files(file_set : DownloadSet) -> bool:
	for file in file_set.values():
		file_path = file.get('path')
		file_name = os.path.basename(file_path)

		if not validate_file(file_path):
			logger.error(translator.get('validating_file_failed').format(file_name = file_name), __name__)

			if remove_file(file_path):
				logger.error(translator.get('deleting_corrupt_file').format(file_name = file_name), __name__)

			return False

		logger.debug(translator.get('validating_file_succeeded').format(file_name = file_name), __name__)

	return True


def validate_file(file_path : str) -> bool:
	if get_file_extension(file_path) == '.hash':
		return is_file(file_path)
	return validate_hash(file_path)


def resolve_download_url(base_name : str, file_name : str) -> Optional[str]:
	download_providers = state_manager.get_item('download_providers')

	for download_provider in download_providers:
		download_url = resolve_download_url_by_provider(download_provider, base_name, file_name)
		if download_url:
			return download_url

	return None


def resolve_download_url_by_provider(download_provider : DownloadProvider, base_name : str, file_name : str) -> Optional[str]:
	download_provider_value = facefusion.choices.download_provider_set.get(download_provider)

	for download_provider_url in download_provider_value.get('urls'):
		if ping_static_url(download_provider_url):
			return download_provider_url + download_provider_value.get('path').format(base_name = base_name, file_name = file_name)

	return None
