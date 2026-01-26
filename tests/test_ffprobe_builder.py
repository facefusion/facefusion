from shutil import which

from facefusion import ffprobe_builder
from facefusion.ffprobe_builder import chain, format_to_key_value, format_to_value, run, set_input, show_entries


def test_run() -> None:
	assert run([ '-v', 'error' ]) == [ which('ffprobe'), '-loglevel', 'error', '-v', 'error' ]


def test_chain() -> None:
	assert chain(
		ffprobe_builder.show_entries([ 'sample_rate' ]),
		ffprobe_builder.format_to_value(),
		ffprobe_builder.set_input('audio.mp3')
	) == [ '-show_entries', 'stream=sample_rate', '-of', 'default=noprint_wrappers=1:nokey=1', 'audio.mp3' ]


def test_show_entries() -> None:
	assert show_entries([ 'duration' ]) == [ '-show_entries', 'stream=duration' ]
	assert show_entries([ 'duration', 'sample_rate']) == [ '-show_entries', 'stream=duration,sample_rate' ]


def test_format_to_value() -> None:
	assert format_to_value() == [ '-of', 'default=noprint_wrappers=1:nokey=1' ]


def test_format_to_key_value() -> None:
	assert format_to_key_value() == [ '-of', 'default=noprint_wrappers=1' ]


def test_set_input() -> None:
	assert set_input('input.mp3') == [ 'input.mp3' ]
	assert set_input('input.wav') == [ 'input.wav' ]
