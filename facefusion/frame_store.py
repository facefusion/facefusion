from facefusion.types import FrameStoreSet, VisionFrame, VisionFrameSet

FRAME_STORE_SET : FrameStoreSet = {}


def get_frame_store(source : str) -> VisionFrameSet:
	if source not in FRAME_STORE_SET:
		FRAME_STORE_SET[source] = {}

	return FRAME_STORE_SET.get(source)


def store_frame(source : str, frame_number : int, vision_frame : VisionFrame) -> None:
	frame_store = get_frame_store(source)
	frame_store[frame_number] = vision_frame


def read_frame_range(source : str, frame_start : int, frame_end : int) -> VisionFrameSet:
	frame_store = get_frame_store(source)
	frame_set = {}

	for frame_number in range(frame_start, frame_end + 1):
		if frame_number in frame_store:
			frame_set[frame_number] = frame_store.get(frame_number)

	return frame_set


def evict_frames(source : str, frame_min : int, frame_max : int) -> None:
	frame_store = get_frame_store(source)
	keep_range = range(frame_min, frame_max + 1)
	frame_set = {}

	for frame_number in frame_store:
		if frame_number in keep_range:
			frame_set[frame_number] = frame_store.get(frame_number)

	FRAME_STORE_SET[source] = frame_set


def clear_frame_store() -> None:
	FRAME_STORE_SET.clear()
