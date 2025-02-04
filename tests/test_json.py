import tempfile

from facefusion.json import read_json, write_json


def test_read_json() -> None:
	_, json_path = tempfile.mkstemp(suffix = '.json')

	assert not read_json(json_path)

	write_json(json_path, {})

	assert read_json(json_path) == {}


def test_write_json() -> None:
	_, json_path = tempfile.mkstemp(suffix = '.json')

	assert write_json(json_path, {})
