from typing import Iterator

import numpy
import pytest

from facefusion import session_context, session_manager
from facefusion.face_store import clear, get_faces, init, resolve_lock, set_faces


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()

	yield

	session_context.set_session_id(local_id)


def test_init() -> None:
	local_id = session_context.resolve_local_id()
	vision_frame = numpy.zeros((16, 16, 3), numpy.uint8)

	set_faces(vision_frame, [])
	session_context.set_session_id('session-a')
	init()

	assert get_faces(vision_frame) is None

	set_faces(vision_frame, [])
	session_manager.fork_session()

	assert get_faces(vision_frame) == []

	session_manager.join_session()
	session_context.set_session_id(local_id)

	assert get_faces(vision_frame) == []


def test_get_faces() -> None:
	vision_frame = numpy.zeros((16, 16, 3), numpy.uint8)

	assert get_faces(vision_frame) is None

	set_faces(vision_frame, [])

	assert get_faces(vision_frame) == []


def test_set_faces() -> None:
	vision_frame = numpy.zeros((16, 16, 3), numpy.uint8)

	set_faces(vision_frame, [])
	set_faces(vision_frame, [])

	assert get_faces(vision_frame) == []


def test_resolve_lock() -> None:
	vision_frame = numpy.zeros((16, 16, 3), numpy.uint8)

	assert resolve_lock(vision_frame) is resolve_lock(vision_frame)


def test_clear() -> None:
	vision_frame = numpy.zeros((16, 16, 3), numpy.uint8)

	set_faces(vision_frame, [])
	clear()

	assert get_faces(vision_frame) is None
