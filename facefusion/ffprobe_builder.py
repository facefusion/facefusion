import itertools
import shutil
from typing import List

from facefusion.types import Command


def run(commands : List[Command]) -> List[Command]:
	return [ shutil.which('ffprobe'), '-loglevel', 'error' ] + commands


def chain(*commands : List[Command]) -> List[Command]:
	return list(itertools.chain(*commands))


def select_audio_stream(index : int) -> List[Command]:
	return [ '-select_streams', 'a:' + str(index) ]


def show_stream_entries(entries : List[str]) -> List[Command]:
	return [ '-show_entries', 'stream=' + ','.join(entries) ]


def format_to_value() -> List[Command]:
	return [ '-of', 'default=noprint_wrappers=1:nokey=1' ]


def format_to_key_value() -> List[Command]:
	return [ '-of', 'default=noprint_wrappers=1' ]


def set_input(input_path : str) -> List[Command]:
	return [ input_path ]
