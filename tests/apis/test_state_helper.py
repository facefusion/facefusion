from typing import cast

from facefusion.apis.state_helper import normalize_argument_value
from facefusion.types import StateKey


def test_normalize_argument_value() -> None:
	assert normalize_argument_value(cast(StateKey, 'face_selector_maps'), [ '0:0 to 100:1' ]) == [ '0:0 to 100:1' ]
	assert normalize_argument_value(cast(StateKey, 'face_selector_maps'), []) is None
	assert normalize_argument_value(cast(StateKey, 'face_selector_maps'), [ [ '0:0' ] ]) is None
	assert normalize_argument_value(cast(StateKey, 'face_selector_maps'), 'invalid') is None
