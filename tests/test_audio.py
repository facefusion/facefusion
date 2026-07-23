
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager
from facefusion.audio import get_audio_frame, read_static_audio
from facefusion.download import conditional_download
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
			ffmpeg_builder.set_output(get_test_example_file('source.wav'))
		)
	)


def test_get_audio_frame() -> None:
	assert get_audio_frame(get_test_example_file('source.mp3'), 25).shape == (80, 16)
	assert get_audio_frame(get_test_example_file('source.wav'), 25).shape == (80, 16)
	assert get_audio_frame('invalid', 25) is None


def test_read_static_audio() -> None:
	assert len(read_static_audio(get_test_example_file('source.mp3'), 25)) == 280
	assert len(read_static_audio(get_test_example_file('source.wav'), 25)) == 280
	assert read_static_audio('invalid', 25) is None
