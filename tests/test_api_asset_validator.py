import pytest

from facefusion.apis.asset_validator import validate_frame_index, validate_resolution, validate_subject


def test_validate_subject() -> None:
	assert validate_subject('frame') is True
	assert validate_subject('face') is True
	assert validate_subject('invalid') is False


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


@pytest.mark.parametrize('frame_index_total, expected',
[
	(0, False),
	(1, True),
	(100, True),
	(101, False)
])
def test_validate_frame_index(frame_index_total : int, expected : bool) -> None:
	assert validate_frame_index([ '0' ] * frame_index_total) is expected
