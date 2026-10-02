
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_audio_metadata, extract_static_audio_metadata, extract_video_fps, extract_video_metadata, parse_entries, probe_audio_entries, probe_format_entries, probe_video_entries
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

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

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vf',
				'fps=30000/1001'
			],
			ffmpeg_builder.set_video_duration(1),
			ffmpeg_builder.set_output(get_test_example_file('target-240p-1s-29.97fps.mp4'))
		)
	)


def test_parse_entries() -> None:
	assert parse_entries('width=426\nheight=226\n'.encode()) == { 'width': '426', 'height': '226' }
	assert parse_entries('filter=scale=426:226'.encode()) == { 'filter': 'scale=426:226' }
	assert parse_entries('invalid\nwidth=426'.encode()) == { 'width': '426' }
	assert parse_entries('invalid'.encode()) == {}
	assert parse_entries(bytes()) == {}


def test_probe_audio_entries() -> None:
	assert probe_audio_entries(get_test_example_file('source.mp3'), [ 'sample_rate', 'channels' ]) == { 'sample_rate': '44100', 'channels': '1' }
	assert probe_audio_entries(get_test_example_file('target-240p.mp4'), [ 'sample_rate' ]) == {}
	assert probe_audio_entries('invalid', [ 'sample_rate' ]) == {}


def test_probe_video_entries() -> None:
	assert probe_video_entries(get_test_example_file('target-240p.mp4'), [ 'width', 'height' ]) == { 'width': '426', 'height': '226' }
	assert probe_video_entries(get_test_example_file('source.mp3'), [ 'width' ]) == {}
	assert probe_video_entries('invalid', [ 'width' ]) == {}


def test_probe_format_entries() -> None:
	assert probe_format_entries(get_test_example_file('target-240p.mp4'), [ 'duration' ]) == { 'duration': '10.800000' }
	assert probe_format_entries('invalid', [ 'duration' ]) == {}


def test_extract_static_audio_metadata() -> None:
	audio_metadata = extract_static_audio_metadata(get_test_example_file('source.mp3'))

	assert audio_metadata.get('sample_rate') == 44100
	assert audio_metadata.get('channel_total') == 1
	assert extract_static_audio_metadata(get_test_example_file('source.mp3')) is audio_metadata


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
	assert video_metadata.get('frame_total') == 270
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

	video_metadata = extract_video_metadata(get_test_example_file('target-240p-1s-29.97fps.mp4'))

	assert video_metadata.get('fps') == 30000 / 1001
	assert video_metadata.get('duration') == 1.001
	assert video_metadata.get('frame_total') == 30


def test_extract_video_fps() -> None:
	assert extract_video_fps({ 'avg_frame_rate': '25/1', 'r_frame_rate': '50/1' }) == 25.0
	assert extract_video_fps({ 'avg_frame_rate': '30000/1001', 'r_frame_rate': '30000/1001' }) == 30000 / 1001
	assert extract_video_fps({ 'avg_frame_rate': '0/0', 'r_frame_rate': '30/1' }) == 30.0
	assert extract_video_fps({ 'avg_frame_rate': '25/0', 'r_frame_rate': '60/1' }) == 60.0
	assert extract_video_fps({ 'avg_frame_rate': '0/1', 'r_frame_rate': '50/1' }) == 50.0
	assert extract_video_fps({ 'r_frame_rate': '24/1' }) == 24.0
	assert extract_video_fps({ 'avg_frame_rate': 'invalid', 'r_frame_rate': 'invalid' }) == 0.0
	assert extract_video_fps({ 'avg_frame_rate': '0/0', 'r_frame_rate': '0/0' }) == 0.0
	assert extract_video_fps({}) == 0.0
