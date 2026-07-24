import numpy
import pytest

from facefusion.frame_store import clear_frame_store, evict_frames, get_frame_store, read_frame_range, store_frame


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_frame_store()


def test_get_frame_store() -> None:
	frame_store = get_frame_store('target.mp4')

	assert frame_store == {}
	assert get_frame_store('target.mp4') is frame_store


def test_store_frame() -> None:
	target_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	store_frame('target.mp4', 5, target_frame)

	assert get_frame_store('target.mp4').get(5) is target_frame


def test_read_frame_range() -> None:
	target_frame = numpy.zeros((2, 2, 3), numpy.uint8)

	for frame_number in range(0, 5):
		store_frame('target.mp4', frame_number, target_frame)

	assert sorted(read_frame_range('target.mp4', 1, 3)) == [ 1, 2, 3 ]
	assert read_frame_range('target.mp4', 8, 12) == {}


def test_read_frame_range_overlap() -> None:
	target_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	store_frame('target.mp4', 2, target_frame)

	assert read_frame_range('target.mp4', 0, 4).get(2) is target_frame
	assert read_frame_range('target.mp4', 2, 6).get(2) is target_frame


def test_evict_frames() -> None:
	target_frame = numpy.zeros((2, 2, 3), numpy.uint8)

	for frame_number in range(0, 10):
		store_frame('target.mp4', frame_number, target_frame)

	evict_frames('target.mp4', 4, 6)

	assert sorted(get_frame_store('target.mp4')) == [ 4, 5, 6 ]


def test_clear_frame_store() -> None:
	target_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	store_frame('target.mp4', 0, target_frame)
	clear_frame_store()

	assert get_frame_store('target.mp4') == {}
