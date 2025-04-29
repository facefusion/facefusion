from typing import List, Optional

from facefusion.types import Fps, Padding


def normalize_padding(padding : Optional[List[int]]) -> Optional[Padding]:
	if padding and len(padding) == 1:
		return tuple([ padding[0] ] * 4) #type:ignore[return-value]
	if padding and len(padding) == 2:
		return tuple([ padding[0], padding[1], padding[0], padding[1] ]) #type:ignore[return-value]
	if padding and len(padding) == 3:
		return tuple([ padding[0], padding[1], padding[2], padding[1] ]) #type:ignore[return-value]
	if padding and len(padding) == 4:
		return tuple(padding) #type:ignore[return-value]
	return None


def normalize_fps(fps : Optional[float]) -> Optional[Fps]:
	if isinstance(fps, (int, float)):
		return max(1.0, min(fps, 60.0))
	return None
