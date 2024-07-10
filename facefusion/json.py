import json
from typing import Optional

from facefusion.filesystem import is_file
from facefusion.typing import Content


def is_json(json_path : str) -> bool:
	if is_file(json_path):
		return read_json(json_path) is not None
	return False


def read_json(json_path : str) -> Optional[Content]:
	try:
		with open(json_path, 'r') as json_file:
			return json.load(json_file)
	except json.JSONDecodeError:
		return None


def write_json(json_path : str, content : Content) -> bool:
	with open(json_path, 'w') as json_file:
		json.dump(content, json_file, indent = 4)
	return is_json(json_path)
