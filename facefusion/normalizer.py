from typing import List, Optional
import os

from facefusion.filesystem import is_file, is_directory
from facefusion.typing import Padding


def normalize_output_path(source_paths : List[str], target_path : str, output_path : str) -> Optional[str]:
	if is_file(target_path) and is_directory(output_path):
		target_name, target_extension = os.path.splitext(os.path.basename(target_path))
		if source_paths and is_file(source_paths[0]):
			source_name, _ = os.path.splitext(os.path.basename(source_paths[0]))
			return os.path.join(output_path, source_name + '-' + target_name + target_extension)
		return os.path.join(output_path, target_name + target_extension)
	if is_file(target_path) and output_path:
		_, target_extension = os.path.splitext(os.path.basename(target_path))
		output_name, output_extension = os.path.splitext(os.path.basename(output_path))
		output_directory_path = os.path.dirname(output_path)
		if is_directory(output_directory_path) and output_extension:
			return os.path.join(output_directory_path, output_name + target_extension)
		return None
	return output_path


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
