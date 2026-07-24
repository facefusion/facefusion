import pytest

from facefusion import process_manager
from facefusion.download import conditional_download
from facefusion.frame_store import clear_frame_store, flush_frames, get_frame_store, select_frame_range, store_frame
from facefusion.vision import read_video_frame
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_frame_store()


def test_get_frame_store() -> None:
	frame_store = get_frame_store('reader-1')

	assert frame_store == {}
	assert get_frame_store('reader-1') is frame_store


def test_store_frame() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)
	store_frame('reader-1', 5, target_frame)

	assert get_frame_store('reader-1').get(5) is target_frame


def test_select_frame_range() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)

	for frame_number in range(0, 5):
		store_frame('reader-1', frame_number, target_frame)

	assert sorted(select_frame_range('reader-1', 1, 3)) == [ 1, 2, 3 ]
	assert select_frame_range('reader-1', 8, 12) == {}


def test_select_frame_range_overlap() -> None:
	first_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)
	fifth_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 5)
	store_frame('reader-1', 2, first_frame)
	store_frame('reader-1', 5, fifth_frame)

	assert select_frame_range('reader-1', 0, 4).get(2) is first_frame
	assert select_frame_range('reader-1', 2, 6).get(2) is first_frame
	assert select_frame_range('reader-1', 2, 6).get(5) is fifth_frame


def test_flush_frames() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)

	for frame_number in range(0, 10):
		store_frame('reader-1', frame_number, target_frame)

	flush_frames('reader-1', 4, 6)

	assert sorted(get_frame_store('reader-1')) == [ 4, 5, 6 ]


def test_clear_frame_store() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)
	store_frame('reader-1', 0, target_frame)
	clear_frame_store()

	assert get_frame_store('reader-1') == {}
