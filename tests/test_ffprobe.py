
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_audio_metadata, extract_video_metadata
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
			ffmpeg_builder.set_video_duration(1.9),
			ffmpeg_builder.set_audio_sample_rate(48000),
			ffmpeg_builder.set_audio_channel_total(2),
			ffmpeg_builder.set_output(get_test_example_file('source-48000khz-2ch.wav'))
		)
	)
	for video_format in [ 'mkv', 'mov' ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.set_video_duration(1),
				ffmpeg_builder.set_output(get_test_example_file('target-240p-1s.' + video_format))
			)
		)


def test_extract_audio_metadata() -> None:
	audio_metadata = extract_audio_metadata(get_test_example_file('source.mp3'))

	assert audio_metadata.get('sample_rate') == 44100
	assert audio_metadata.get('channel_total') == 1
	assert audio_metadata.get('frame_total') == 167040
	assert audio_metadata.get('bit_rate') == 128000

	audio_metadata = extract_audio_metadata(get_test_example_file('source-48000khz-2ch.wav'))

	assert audio_metadata.get('sample_rate') == 48000
	assert audio_metadata.get('channel_total') == 2
	assert audio_metadata.get('frame_total') == 91200
	assert audio_metadata.get('bit_rate') == 1536328


def test_extract_video_metadata() -> None:
	video_metadata = extract_video_metadata(get_test_example_file('target-240p.mp4'))

	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('duration') == 10.8
	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('bit_rate') == 141981
	assert video_metadata.get('color_transfer') == 'smpte170m'

	video_metadata = extract_video_metadata(get_test_example_file('target-240p-1s.mkv'))

	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('duration') == 1.0
	assert video_metadata.get('frame_total') == 25
	assert video_metadata.get('resolution') == (426, 226)

	video_metadata = extract_video_metadata(get_test_example_file('target-240p-1s.mov'))

	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('duration') == 1.0
	assert video_metadata.get('resolution') == (426, 226)
