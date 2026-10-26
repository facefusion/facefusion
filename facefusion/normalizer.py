from typing import Any, List, Optional, Tuple

from facefusion.types import Fps, Map


def normalize_color(color : Any) -> Optional[Tuple[int, int, int, int]]:
	if isinstance(color, (list, tuple)):
		if color and len(color) == 1:
			return tuple([color[0], color[0], color[0], 255])
		if color and len(color) == 2:
			return tuple([color[0], color[1], color[0], 255])
		if color and len(color) == 3:
			return tuple([color[0], color[1], color[2], 255])
		if color and len(color) == 4:
			return tuple(color)
	return None


def normalize_space(space : Any) -> Optional[Tuple[int, int, int, int]]:
	if isinstance(space, (list, tuple)):
		if space and len(space) == 1:
			return tuple([space[0]] * 4)
		if space and len(space) == 2:
			return tuple([space[0], space[1], space[0], space[1]])
		if space and len(space) == 3:
			return tuple([space[0], space[1], space[2], space[1]])
		if space and len(space) == 4:
			return tuple(space)
	return None


def normalize_maps(maps : Any) -> Optional[List[Map]]:
	temp_maps = []

	if isinstance(maps, list):
		for __map__ in maps:
			if isinstance(__map__, (list, tuple)) and len(__map__) == 4:
				temp_maps.append(tuple(__map__))

	if temp_maps:
		return temp_maps

	return None


def normalize_range(total : int, start : Optional[int], end : Optional[int]) -> Tuple[int, int]:
	if isinstance(start, int):
		start = max(0, min(start, total))
	if isinstance(end, int):
		end = max(0, min(end, total))
	if isinstance(start, int) and isinstance(end, int):
		return start, end
	if isinstance(start, int):
		return start, total
	if isinstance(end, int):
		return 0, end
	return 0, total


def normalize_fps(fps : Any) -> Optional[Fps]:
	if isinstance(fps, (int, float)):
		return max(1.0, min(fps, 60.0))
	return None
