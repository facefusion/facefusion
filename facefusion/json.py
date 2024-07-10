import json
from typing import Any, Dict, Optional

from facefusion.filesystem import is_file


def is_json(json_path : str) -> bool:
	if is_file(json_path):
		try:
			with open(json_path, 'r') as file:
				json.load(file)
			return True
		except json.JSONDecodeError:
			return False
	return False


def read_json(json_path : str) -> Optional[Dict[Any, Any]]:
	with open(json_path, 'r') as json_file:
		return json.load(json_file)


def write_json(json_path : str, data : Dict[Any, Any]) -> bool:
	with open(json_path, 'w') as json_file:
		json.dump(data, json_file, indent = 4)
	return is_json(json_path)
