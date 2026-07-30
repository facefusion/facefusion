import tempfile

import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_video_metadata
from facefusion.frame_store import get_frame_store
from facefusion.temp_helper import create_temp_directory, get_temp_file_path
from facefusion.video_manager import clear_video_pool, close_video_reader, close_video_writer, collect_video_frames, conditional_seek_video_reader, drain_video_reader, get_reader, get_writer, read_video_frame, read_video_frames, seek_video_reader, write_video_frame
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	for video_fps in [ 25, 30 ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.set_video_fps(video_fps),
				ffmpeg_builder.set_output(get_test_example_file('target-240p-' + str(video_fps) + 'fps.mp4'))
			)
		)

	state_manager.init_item('temp_path', tempfile.gettempdir())
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('output_video_encoder', 'libx264')
	state_manager.init_item('output_video_quality', 80)
	state_manager.init_item('output_video_preset', 'veryfast')
	state_manager.init_item('temp_pixel_format', 'bgr24')


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_video_pool()


def test_get_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')
	video_metadata = video_reader.get('metadata')

	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('frame_total') == 270

	assert get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame') is video_reader
	assert not get_reader(get_test_example_file('target-240p-25fps.mp4'), 'select_video_frames').get('id') == video_reader.get('id')


def test_conditional_seek_video_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')
	video_frames = {}

	for frame_number in range(30):
		video_frames[frame_number] = read_video_frame(video_reader)

	for frame_number in [ 5, 17, 29 ]:
		conditional_seek_video_reader(video_reader, frame_number)

		assert numpy.array_equal(read_video_frame(video_reader), video_frames.get(frame_number)) is True


def test_seek_video_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')
	video_frames = {}

	for frame_number in range(30):
		video_frames[frame_number] = read_video_frame(video_reader)

	for frame_number in [ 5, 17, 29 ]:
		seek_video_reader(video_reader, frame_number)

		assert numpy.array_equal(read_video_frame(video_reader), video_frames.get(frame_number)) is True


def test_drain_video_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')

	drain_video_reader(video_reader, 10)

	assert video_reader.get('frame_number') == 10

	vision_frame = read_video_frame(video_reader)
	seek_video_reader(video_reader, 10)

	assert numpy.array_equal(vision_frame, read_video_frame(video_reader)) is True


def test_read_video_frame() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')

	assert read_video_frame(video_reader).shape == (226, 426, 3)
	assert video_reader.get('frame_number') == 1

	seek_video_reader(video_reader, 269)

	assert read_video_frame(video_reader).shape == (226, 426, 3)
	assert read_video_frame(video_reader) is None


def test_read_video_frames() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'read_video_frame')

	assert sorted(read_video_frames(video_reader, 0, 4)) == [ 0, 1, 2, 3, 4 ]

	frame_number = video_reader.get('frame_number')

	assert sorted(read_video_frames(video_reader, 1, 3)) == [ 1, 2, 3 ]
	assert video_reader.get('frame_number') == frame_number

	read_video_frames(video_reader, 21, 25)

	assert min(get_frame_store(video_reader.get('id'))) == 17
	assert max(get_frame_store(video_reader.get('id'))) == 25
	assert sorted(read_video_frames(video_reader, 268, 275)) == [ 268, 269 ]


def test_collect_video_frames() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'select_video_frames')

	collect_video_frames(video_reader, 20, 24)

	assert sorted(get_frame_store(video_reader.get('id'))) == [ 20, 21, 22, 23, 24 ]
	assert video_reader.get('frame_number') == 25


def test_close_video_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'), 'select_video_frames')

	read_video_frames(video_reader, 0, 4)
	close_video_reader(video_reader)

	if is_windows():
		assert video_reader.get('process').returncode == 1

	if is_linux() or is_macos():
		assert video_reader.get('process').returncode == -9


def test_get_writer() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)

	assert get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0) is video_writer


def test_write_video_frame() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_reader = get_reader(target_path, 'read_video_frame')
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)

	for frame_number in range(25):
		write_video_frame(video_writer, read_video_frame(video_reader))

	assert close_video_writer(video_writer) is True

	video_metadata = extract_video_metadata(get_temp_file_path(target_path))

	assert video_metadata.get('duration') == 1.0
	assert video_metadata.get('frame_total') == 25
	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('color_transfer') == 'bt709'


def test_close_video_writer() -> None:
	target_path = get_test_example_file('target-240p-30fps.mp4')
	create_temp_directory(target_path)
	video_reader = get_reader(target_path, 'read_video_frame')
	video_writer = get_writer(target_path, 30.0, (426, 226), (426, 226), 30.0)

	write_video_frame(video_writer, read_video_frame(video_reader))

	assert close_video_writer(video_writer) is True


def test_clear_video_pool() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_reader = get_reader(target_path, 'select_video_frames')
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)

	read_video_frames(video_reader, 0, 4)
	write_video_frame(video_writer, read_video_frame(video_reader))
	clear_video_pool()

	if is_windows():
		assert video_reader.get('process').returncode == 1

	if is_linux() or is_macos():
		assert video_reader.get('process').returncode == -9

	assert video_writer.get('process').returncode == 0
