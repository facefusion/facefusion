from typing import List, Optional

from facefusion.types import Color, Fps, Padding


def normalize_color(channels : Optional[List[int]]) -> Optional[Color]:
	if channels and len(channels) == 1:
		return tuple([ channels[0], channels[0], channels[0], 255 ]) #type:ignore[return-value]
	if channels and len(channels) == 2:
		return tuple([ channels[0], channels[1], channels[0], 255 ]) #type:ignore[return-value]
	if channels and len(channels) == 3:
		return tuple([ channels[0], channels[1], channels[2], 255 ]) #type:ignore[return-value]
	if channels and len(channels) == 4:
		return tuple(channels) #type:ignore[return-value]
	return None


def normalize_space(spaces : Optional[List[int]]) -> Optional[Padding]:
	if spaces and len(spaces) == 1:
		return tuple([spaces[0]] * 4) #type:ignore[return-value]
	if spaces and len(spaces) == 2:
		return tuple([spaces[0], spaces[1], spaces[0], spaces[1]]) #type:ignore[return-value]
	if spaces and len(spaces) == 3:
		return tuple([spaces[0], spaces[1], spaces[2], spaces[1]]) #type:ignore[return-value]
	if spaces and len(spaces) == 4:
		return tuple(spaces) #type:ignore[return-value]
	return None


def normalize_fps(fps : Optional[float]) -> Optional[Fps]:
	if isinstance(fps, (int, float)):
		return max(1.0, min(fps, 60.0))
	return None
