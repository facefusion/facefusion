import itertools
import shutil
from typing import List

from facefusion.types import Command


def run(commands : List[Command]) -> List[Command]:
	return [ shutil.which('ffprobe'), '-loglevel', 'error' ] + commands


def chain(*commands : List[Command]) -> List[Command]:
	return list(itertools.chain(*commands))


def select_stream(stream : str) -> List[Command]:
	return [ '-select_streams', stream ]


def show_stream_entries(entries : List[str], side_data : str = '') -> List[Command]:
	selection = 'stream=' + ','.join(entries)
	if side_data:
		selection += ':stream_side_data=' + side_data
	return [ '-show_entries', selection ]


def show_format_entries(entries : List[str]) -> List[Command]:
	return [ '-show_entries', 'format=' + ','.join(entries) ]


def format_to_key_value() -> List[Command]:
	return [ '-of', 'default=noprint_wrappers=1' ]


def set_input(input_path : str) -> List[Command]:
	return [ '-i', input_path ]
