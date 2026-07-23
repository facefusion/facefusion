import tempfile

import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_video_metadata
from facefusion.temp_helper import create_temp_directory, get_temp_file_path
from facefusion.video_manager import clear_video_pool, close_video_writer, conditional_set_video_reader_position, get_reader, get_writer, read_video_reader_frame, read_video_reader_window, refresh_video_reader, write_video_writer_frame
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


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_video_pool()


def test_get_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))
	video_metadata = video_reader.get('metadata')

	assert video_metadata.get('resolution') == (426, 226)
	assert video_metadata.get('fps') == 25.0
	assert video_metadata.get('frame_total') == 270
	assert video_reader.get('position') == 0
	assert get_reader(get_test_example_file('target-240p-25fps.mp4')) is video_reader


def test_conditional_set_video_reader_position() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))

	conditional_set_video_reader_position(video_reader, 50)

	assert video_reader.get('position') == 50

	conditional_set_video_reader_position(video_reader, 10)

	assert video_reader.get('position') == 10

	conditional_set_video_reader_position(video_reader, 200)

	assert video_reader.get('position') == 200


def test_refresh_video_reader() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))
	sequential_frames = {}

	for frame_number in range(30):
		sequential_frames[frame_number] = read_video_reader_frame(video_reader)

	for frame_number in [ 5, 17, 29 ]:
		refresh_video_reader(video_reader, frame_number)
		vision_frame = read_video_reader_frame(video_reader)

		assert numpy.array_equal(vision_frame, sequential_frames.get(frame_number)) is True


def test_read_video_reader_frame() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))
	vision_frame = read_video_reader_frame(video_reader)

	assert vision_frame.shape == (226, 426, 3)
	assert video_reader.get('position') == 1

	conditional_set_video_reader_position(video_reader, 269)
	vision_frame = read_video_reader_frame(video_reader)

	assert vision_frame.shape == (226, 426, 3)
	assert read_video_reader_frame(video_reader) is None


def test_read_video_reader_window() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))
	frame_set = read_video_reader_window(video_reader, 0, 4)

	assert sorted(frame_set) == [ 0, 1, 2, 3, 4 ]

	frame_set = read_video_reader_window(video_reader, 100, 104)

	assert sorted(frame_set) == [ 100, 101, 102, 103, 104 ]

	frame_set = read_video_reader_window(video_reader, 268, 275)

	assert sorted(frame_set) == [ 268, 269 ]


def test_evict_video_reader_buffer() -> None:
	video_reader = get_reader(get_test_example_file('target-240p-25fps.mp4'))
	read_video_reader_window(video_reader, 0, 4)
	frame_set = read_video_reader_window(video_reader, 21, 25)

	assert min(frame_set) == 5
	assert max(frame_set) == 25


def test_get_writer() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)

	assert get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0) is video_writer


def test_write_video_writer_frame() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_reader = get_reader(target_path)
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)

	for frame_number in range(25):
		vision_frame = read_video_reader_frame(video_reader)
		write_video_writer_frame(video_writer, vision_frame)

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
	video_reader = get_reader(target_path)
	video_writer = get_writer(target_path, 30.0, (426, 226), (426, 226), 30.0)
	vision_frame = read_video_reader_frame(video_reader)
	write_video_writer_frame(video_writer, vision_frame)

	assert close_video_writer(video_writer) is True


def test_clear_video_pool() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')
	create_temp_directory(target_path)
	video_reader = get_reader(target_path)
	video_writer = get_writer(target_path, 25.0, (426, 226), (426, 226), 25.0)
	clear_video_pool()

	assert video_reader.get('process').returncode == -9
	assert video_writer.get('process').returncode == -9
