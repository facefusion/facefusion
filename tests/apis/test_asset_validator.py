from typing import List, cast

import pytest

from facefusion.apis.asset_validator import validate_asset_id, validate_asset_ids, validate_frame_index, validate_subject
from facefusion.types import AssetId


def test_validate_subject() -> None:
	assert validate_subject('frame') is True
	assert validate_subject('face') is True
	assert validate_subject('invalid') is False


@pytest.mark.parametrize('frame_index_total, expected',
[
	(0, False),
	(1, True),
	(100, True),
	(101, False)
])
def test_validate_frame_index(frame_index_total : int, expected : bool) -> None:
	assert validate_frame_index([ '0' ] * frame_index_total) is expected


def test_validate_asset_id() -> None:
	assert validate_asset_id('invalid') is True
	assert validate_asset_id(cast(AssetId, [ 'invalid' ])) is False


def test_validate_asset_ids() -> None:
	assert validate_asset_ids([ 'invalid' ]) is True
	assert validate_asset_ids(cast(List[AssetId], 'invalid')) is False
	assert validate_asset_ids(cast(List[AssetId], [ [ 'invalid' ] ])) is False
