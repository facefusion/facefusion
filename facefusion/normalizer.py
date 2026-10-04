from typing import Any, Optional, Tuple

from facefusion.types import Color, Fps, Space


def normalize_color(channels : Any) -> Optional[Color]:
	if isinstance(channels, (list, tuple)):
		if channels and len(channels) == 1:
			return tuple([ channels[0], channels[0], channels[0], 255 ])
		if channels and len(channels) == 2:
			return tuple([ channels[0], channels[1], channels[0], 255 ])
		if channels and len(channels) == 3:
			return tuple([ channels[0], channels[1], channels[2], 255 ])
		if channels and len(channels) == 4:
			return tuple(channels)
	return None


def normalize_space(spaces : Any) -> Optional[Space]:
	if isinstance(spaces, (list, tuple)):
		if spaces and len(spaces) == 1:
			return tuple([spaces[0]] * 4)
		if spaces and len(spaces) == 2:
			return tuple([ spaces[0], spaces[1], spaces[0], spaces[1] ])
		if spaces and len(spaces) == 3:
			return tuple([ spaces[0], spaces[1], spaces[2], spaces[1] ])
		if spaces and len(spaces) == 4:
			return tuple(spaces)
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
