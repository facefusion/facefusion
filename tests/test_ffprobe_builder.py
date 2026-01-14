from shutil import which

from facefusion import ffprobe_builder
from facefusion.ffprobe_builder import chain, run, select_audio_stream, set_error_level, set_input, set_output_key_value, set_output_value_only, show_stream_entries


def test_run() -> None:
	assert run([]) == [ which('ffprobe'), '-loglevel', 'error' ]
	assert run([ '-v', 'error' ]) == [ which('ffprobe'), '-loglevel', 'error', '-v', 'error' ]


def test_chain() -> None:
	assert chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(0)
	) == [ '-v', 'error', '-select_streams', 'a:0' ]
	assert chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(0),
		ffprobe_builder.show_stream_entries([ 'sample_rate' ]),
		ffprobe_builder.set_output_value_only(),
		ffprobe_builder.set_input('audio.mp3')
	) == [ '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=sample_rate', '-of', 'default=noprint_wrappers=1:nokey=1', 'audio.mp3' ]


def test_set_error_level() -> None:
	assert set_error_level() == [ '-v', 'error' ]


def test_select_audio_stream() -> None:
	assert select_audio_stream(0) == [ '-select_streams', 'a:0' ]


def test_show_entries() -> None:
	assert show_stream_entries([ 'sample_rate' ]) == [ '-show_entries', 'stream=sample_rate' ]
	assert show_stream_entries([ 'channels' ]) == [ '-show_entries', 'stream=channels' ]
	assert show_stream_entries([ 'duration', 'sample_rate' ]) == [ '-show_entries', 'stream=duration,sample_rate' ]


def test_set_output_value_only() -> None:
	assert set_output_value_only() == [ '-of', 'default=noprint_wrappers=1:nokey=1' ]


def test_set_output_key_value() -> None:
	assert set_output_key_value() == [ '-of', 'default=noprint_wrappers=1' ]


def test_set_input() -> None:
	assert set_input('audio.mp3') == [ 'audio.mp3' ]
	assert set_input('/path/to/audio.wav') == [ '/path/to/audio.wav' ]
