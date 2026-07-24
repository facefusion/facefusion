import pytest

from facefusion import process_manager
from facefusion.download import conditional_download
from facefusion.frame_store import clear_frames, get_frame_store, reduce_frames, select_frame_set, set_frame
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
	clear_frames('reader-1')
	clear_frames('reader-2')


def test_get_frame_store() -> None:
	frame_store = get_frame_store('reader-1')

	assert frame_store == {}
	assert get_frame_store('reader-1') is frame_store


def test_set_frame() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)

	set_frame('reader-1', 5, target_frame)

	assert get_frame_store('reader-1').get(5) is target_frame


def test_select_frame_set() -> None:
	first_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)
	fifth_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 5)

	set_frame('reader-1', 2, first_frame)
	set_frame('reader-1', 5, fifth_frame)

	assert sorted(select_frame_set('reader-1', 0, 4)) == [ 2 ]
	assert select_frame_set('reader-1', 0, 4).get(2) is first_frame
	assert sorted(select_frame_set('reader-1', 2, 6)) == [ 2, 5 ]
	assert select_frame_set('reader-1', 2, 6).get(5) is fifth_frame
	assert select_frame_set('reader-1', 8, 12) == {}


def test_reduce_frames() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)

	for frame_number in range(0, 10):
		set_frame('reader-1', frame_number, target_frame)

	reduce_frames('reader-1', 4, 6)

	assert sorted(get_frame_store('reader-1')) == [ 4, 5, 6 ]


def test_clear_frames() -> None:
	target_frame = read_video_frame(get_test_example_file('target-240p.mp4'), 0)

	set_frame('reader-1', 0, target_frame)
	set_frame('reader-2', 0, target_frame)
	clear_frames('reader-1')

	assert get_frame_store('reader-1') == {}
	assert get_frame_store('reader-2').get(0) is target_frame
