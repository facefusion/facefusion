from facefusion.types import FrameStoreSet, VisionFrame, VisionFrameSet

FRAME_STORE_SET : FrameStoreSet = {}


def get_frame_store(id : str) -> VisionFrameSet:
	if id not in FRAME_STORE_SET:
		FRAME_STORE_SET[id] = {}

	return FRAME_STORE_SET.get(id)


def set_frame(id : str, frame_number : int, vision_frame : VisionFrame) -> None:
	frame_store = get_frame_store(id)
	frame_store[frame_number] = vision_frame


def select_frame_set(id : str, frame_start : int, frame_end : int) -> VisionFrameSet:
	frame_store = get_frame_store(id)
	frame_set = {}

	for frame_number in range(frame_start, frame_end + 1):
		if frame_number in frame_store:
			frame_set[frame_number] = frame_store.get(frame_number)

	return frame_set


def reduce_frames(id : str, frame_min : int, frame_max : int) -> None:
	FRAME_STORE_SET[id] = select_frame_set(id, frame_min, frame_max)


def clear_frames(id : str) -> None:
	if id in FRAME_STORE_SET:
		del FRAME_STORE_SET[id]
