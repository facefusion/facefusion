import cv2
import numpy
import pytest

from facefusion.apis.media_validator import validate_media_resolution, validate_resolution


@pytest.mark.parametrize('resolution, expected',
[
	('63x63', False),
	('64x64', True),
	('4096x4096', True),
	('4097x4097', False),
	('invalid', False)
])
def test_validate_resolution(resolution : str, expected : bool) -> None:
	assert validate_resolution(resolution) is expected


def test_validate_media_resolution() -> None:
	assert validate_media_resolution(cv2.imencode('.png', numpy.zeros((4096, 4096, 3), numpy.uint8))[1].tobytes()) is True
	assert validate_media_resolution(cv2.imencode('.png', numpy.zeros((4098, 4098, 3), numpy.uint8))[1].tobytes()) is False
	assert validate_media_resolution(bytes([ 1, 2, 3 ])) is False
