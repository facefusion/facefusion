from typing import Optional, Tuple


def restrict_trim_frame(frame_total : int, trim_frame_start : Optional[int], trim_frame_end : Optional[int]) -> Tuple[int, int]:
	if isinstance(trim_frame_start, int):
		trim_frame_start = max(0, min(trim_frame_start, frame_total))
	if isinstance(trim_frame_end, int):
		trim_frame_end = max(0, min(trim_frame_end, frame_total))

	if isinstance(trim_frame_start, int) and isinstance(trim_frame_end, int):
		return trim_frame_start, trim_frame_end
	if isinstance(trim_frame_start, int):
		return trim_frame_start, frame_total
	if isinstance(trim_frame_end, int):
		return 0, trim_frame_end

	return 0, frame_total
