import os
import tempfile

from facefusion.json import read_json, write_json


def test_read_json() -> None:
	file_descriptor, json_path = tempfile.mkstemp(suffix = '.json')
	os.close(file_descriptor)

	assert read_json(json_path) is None
	assert read_json('invalid') is None

	write_json(json_path, {})

	assert read_json(json_path) == {}

	write_json(json_path,
	{
		'name': 'facefusion',
		'steps':
		[
			1,
			2
		]
	})

	assert read_json(json_path) ==\
	{
		'name': 'facefusion',
		'steps':
		[
			1,
			2
		]
	}


def test_write_json() -> None:
	file_descriptor, json_path = tempfile.mkstemp(suffix = '.json')
	os.close(file_descriptor)

	assert write_json(json_path, {}) is True

	with open(json_path) as json_file:
		assert json_file.read() == '{}'
