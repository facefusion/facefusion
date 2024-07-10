import json
import os
import os.path
import tempfile

from facefusion.json import is_json, read_json, write_json


def create_valid_json() -> str:
	temp_file_descriptor, temp_json_path = tempfile.mkstemp(suffix = '.json')
	with os.fdopen(temp_file_descriptor, 'w') as json_file:
		json.dump({}, json_file)
	return temp_json_path


def create_invalid_json() -> str:
	temp_json_path = tempfile.mkstemp(suffix = '.json')[1]
	return temp_json_path


def test_is_json() -> None:
	assert is_json(create_valid_json())
	assert not is_json(create_invalid_json())


def test_read_json() -> None:
	assert read_json(create_valid_json()) == {}
	assert not read_json(create_invalid_json())


def test_write_json() -> None:
	temp_json_path = tempfile.mkstemp(suffix = '.json')[1]
	assert write_json(temp_json_path, {})
