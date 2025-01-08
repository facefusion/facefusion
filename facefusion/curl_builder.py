import shutil

from facefusion.typing import Commands


def run(commands : Commands) -> Commands:
	return [ shutil.which('curl'), '--silent', '--insecure', '--location' ] + commands


def head(url : str) -> Commands:
	return [ '-I', url ]


def download(url : str, download_file_path : str) -> Commands:
	return [ '--create-dirs', '--continue-at', '-', '--output', download_file_path, url ]


def set_timeout(timeout : int) -> Commands:
	return [ '--connect-timeout', str(timeout) ]
