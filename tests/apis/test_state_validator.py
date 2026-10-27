from argparse import ArgumentParser
from typing import cast

import pytest

from facefusion import capability_store, state_manager
from facefusion.apis.state_validator import validate_argument_key, validate_argument_value, validate_face_pointers, validate_face_selector_maps
from facefusion.types import StateKey


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	program = ArgumentParser()
	capability_store.register_capability_set(
		[
			program.add_argument(
				'--execution-providers',
				nargs = '+',
				choices = [ 'cpu', 'cuda' ]
			)
		],
		scopes = [ 'api' ],
		groups = [ 'execution' ])


def test_validate_argument_key() -> None:
	assert validate_argument_key(cast(StateKey, 'execution_providers')) is True
	assert validate_argument_key(cast(StateKey, 'invalid')) is False


def test_validate_argument_value() -> None:
	assert validate_argument_value(cast(StateKey, 'execution_providers'), [ 'cpu' ]) is True
	assert validate_argument_value(cast(StateKey, 'execution_providers'), [ 'invalid' ]) is False
	assert validate_argument_value(cast(StateKey, 'execution_providers'), 'invalid') is False


def test_validate_face_selector_maps() -> None:
	assert validate_face_selector_maps([ { 'source_faces': [ { 'frame_index': 0, 'face_position': 0 } ], 'reference_faces': [ { 'frame_index': 120, 'face_position': 1 } ] } ]) is True
	assert validate_face_selector_maps([]) is True
	assert validate_face_selector_maps([ { 'source_faces': [], 'reference_faces': [] } ]) is False
	assert validate_face_selector_maps([ { 'source_faces': [ { 'frame_index': 0, 'face_position': 0 } ] } ]) is False
	assert validate_face_selector_maps('invalid') is False


def test_validate_face_pointers() -> None:
	assert validate_face_pointers([ { 'frame_index': 0, 'face_position': 1 } ]) is True
	assert validate_face_pointers([]) is True
	assert validate_face_pointers([ { 'frame_index': -1, 'face_position': 0 } ]) is False
	assert validate_face_pointers([ { 'frame_index': 1.5, 'face_position': 0 } ]) is False
	assert validate_face_pointers([ { 'frame_index': 0 } ]) is False
	assert validate_face_pointers('invalid') is False
