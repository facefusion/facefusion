import tempfile

from facefusion.json import is_json, read_json, write_json


def test_is_json() -> None:
	_, temp_json_path = tempfile.mkstemp(suffix = '.json')
	assert not is_json(temp_json_path)

	write_json(temp_json_path, {})
	assert is_json(temp_json_path)


def test_read_json() -> None:
	_, temp_json_path = tempfile.mkstemp(suffix = '.json')
	assert not read_json(temp_json_path)

	write_json(temp_json_path, {})
	assert read_json(temp_json_path) == {}


def test_write_json() -> None:
	_, temp_json_path = tempfile.mkstemp(suffix = '.json')
	assert write_json(temp_json_path, {})
