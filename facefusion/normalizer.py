from typing import List, Optional
import hashlib
import os

import facefusion.globals
from facefusion.filesystem import is_directory
from facefusion.typing import Padding, Fps


def normalize_output_path(target_path : Optional[str], output_path : Optional[str]) -> Optional[str]:
	if target_path and output_path:
		target_name, target_extension = os.path.splitext(os.path.basename(target_path))
		if is_directory(output_path):
			output_hash = hashlib.sha1(str(facefusion.globals.__dict__).encode('utf-8')).hexdigest()[:8]
			output_name = target_name + '-' + output_hash
			return os.path.join(output_path, output_name + target_extension)
		output_name, output_extension = os.path.splitext(os.path.basename(output_path))
		output_directory_path = os.path.dirname(output_path)
		if is_directory(output_directory_path) and output_extension:
			return os.path.join(output_directory_path, output_name + target_extension)
	return None


def normalize_padding(padding : Optional[List[int]]) -> Optional[Padding]:
	if padding and len(padding) == 1:
		return tuple([ padding[0], padding[0], padding[0], padding[0] ]) # type: ignore[return-value]
	if padding and len(padding) == 2:
		return tuple([ padding[0], padding[1], padding[0], padding[1] ]) # type: ignore[return-value]
	if padding and len(padding) == 3:
		return tuple([ padding[0], padding[1], padding[2], padding[1] ]) # type: ignore[return-value]
	if padding and len(padding) == 4:
		return tuple(padding) # type: ignore[return-value]
	return None


def normalize_fps(fps : Optional[float]) -> Optional[Fps]:
	if fps is not None:
		if fps < 1.0:
			return 1.0
		if fps > 60.0:
			return 60.0
		return fps
	return None
