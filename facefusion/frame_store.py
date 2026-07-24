from facefusion.types import FrameStoreSet, VisionFrame, VisionFrameSet

FRAME_STORE_SET : FrameStoreSet = {}


def get_frame_store(reader_id : str) -> VisionFrameSet:
	if reader_id not in FRAME_STORE_SET:
		FRAME_STORE_SET[reader_id] = {}

	return FRAME_STORE_SET.get(reader_id)


def store_frame(reader_id : str, frame_number : int, vision_frame : VisionFrame) -> None:
	frame_store = get_frame_store(reader_id)
	frame_store[frame_number] = vision_frame


def select_frame_range(reader_id : str, frame_start : int, frame_end : int) -> VisionFrameSet:
	frame_store = get_frame_store(reader_id)
	frame_set = {}

	for frame_number in range(frame_start, frame_end + 1):
		if frame_number in frame_store:
			frame_set[frame_number] = frame_store.get(frame_number)

	return frame_set


def flush_frames(reader_id : str, frame_min : int, frame_max : int) -> None:
	frame_store = get_frame_store(reader_id)
	keep_range = range(frame_min, frame_max + 1)
	frame_set = {}

	for frame_number in frame_store:
		if frame_number in keep_range:
			frame_set[frame_number] = frame_store.get(frame_number)

	FRAME_STORE_SET[reader_id] = frame_set


def clear_frame_store() -> None:
	FRAME_STORE_SET.clear()
