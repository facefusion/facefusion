import os
import subprocess
import urllib.request
from typing import List
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from tqdm import tqdm

import facefusion.globals
from facefusion import wording
from facefusion.filesystem import is_file


def conditional_download(download_directory_path : str, urls : List[str]) -> None:
	with ThreadPoolExecutor() as executor:
		for url in urls:
			executor.submit(get_download_size, url)
	for url in urls:
		download_file_path = os.path.join(download_directory_path, os.path.basename(url))
		initial = os.path.getsize(download_file_path) if is_file(download_file_path) else 0
		total = get_download_size(url)
		if initial < total:
			with tqdm(total = total, initial = initial, desc = wording.get('downloading'), unit = 'B', unit_scale = True, unit_divisor = 1024, ascii = ' =', disable = facefusion.globals.log_level in [ 'warn', 'error' ]) as progress:
				subprocess.Popen([ 'curl', '--create-dirs', '--silent', '--insecure', '--location', '--continue-at', '-', '--output', download_file_path, url ])
				current = initial
				while current < total:
					if is_file(download_file_path):
						current = os.path.getsize(download_file_path)
						progress.update(current - progress.n)


@lru_cache(maxsize = None)
def get_download_size(url : str) -> int:
	try:
		response = urllib.request.urlopen(url, timeout = 10)
		return int(response.getheader('Content-Length'))
	except (OSError, ValueError):
		return 0


def is_download_done(url : str, file_path : str) -> bool:
	if is_file(file_path):
		return get_download_size(url) == os.path.getsize(file_path)
	return False
