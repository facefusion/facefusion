import itertools
import shutil
from typing import List

from facefusion.types import Command


def run(commands : List[Command]) -> List[Command]:
	return [ shutil.which('ffprobe'), '-loglevel', 'error' ] + commands


def chain(*commands : List[Command]) -> List[Command]:
	return list(itertools.chain(*commands))


def set_error_level() -> List[Command]:
	return [ '-v', 'error' ]


def select_audio_stream(index : int) -> List[Command]:
	return [ '-select_streams', 'a:{}'.format(index) ]


def show_entries(entries : str) -> List[Command]:
	return [ '-show_entries', entries ]


def set_output_value_only() -> List[Command]:
	return [ '-of', 'default=noprint_wrappers=1:nokey=1' ]


def set_output_key_value() -> List[Command]:
	return [ '-of', 'default=noprint_wrappers=1' ]


def set_input(input_path : str) -> List[Command]:
	return [ input_path ]
