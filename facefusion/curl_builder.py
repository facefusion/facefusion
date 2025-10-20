import itertools
import shutil
from typing import List

from facefusion import metadata
from facefusion.types import Command


def run(commands : List[Command]) -> List[Command]:
	user_agent = metadata.get('name') + '/' + metadata.get('version')

	return [ shutil.which('curl'), '--user-agent', user_agent, '--insecure', '--location', '--silent' ] + commands


def chain(*commands : List[Command]) -> List[Command]:
	return list(itertools.chain(*commands))


def head(url : str) -> List[Command]:
	return [ '-I', url ]


def download(url : str, download_file_path : str) -> List[Command]:
	return [ '--create-dirs', '--continue-at', '-', '--output', download_file_path, url ]


def set_timeout(timeout : int) -> List[Command]:
	return [ '--connect-timeout', str(timeout) ]
