from typing import Any, List, Optional, Tuple

from facefusion.types import Color, Fps, Map, Space


def normalize_color(color : Any) -> Optional[Color]:
	if isinstance(color, (list, tuple)):
		if color and len(color) == 1:
			return tuple([ color[0], color[0], color[0], 255 ])
		if color and len(color) == 2:
			return tuple([ color[0], color[1], color[0], 255 ])
		if color and len(color) == 3:
			return tuple([ color[0], color[1], color[2], 255 ])
		if color and len(color) == 4:
			return tuple(color)
	return None


def normalize_space(space : Any) -> Optional[Space]:
	if isinstance(space, (list, tuple)):
		if space and len(space) == 1:
			return tuple([space[0]] * 4)
		if space and len(space) == 2:
			return tuple([ space[0], space[1], space[0], space[1] ])
		if space and len(space) == 3:
			return tuple([ space[0], space[1], space[2], space[1] ])
		if space and len(space) == 4:
			return tuple(space)
	return None


def normalize_maps(maps : Any) -> Optional[List[Map]]:
	temp_maps : List[Map] = []

	if isinstance(maps, list):
		for __map__ in maps:
			if isinstance(__map__, str):
				temp_maps.append(__map__)

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
