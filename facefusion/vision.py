from typing import Optional
import cv2

from facefusion.typing import Frame


def get_video_frame(video_path : str, frame_number : int = 0) -> Optional[Frame]:
	capture = cv2.VideoCapture(video_path)
	frame_total = capture.get(cv2.CAP_PROP_FRAME_COUNT)
	capture.set(cv2.CAP_PROP_POS_FRAMES, min(frame_total, frame_number - 1))
	has_frame, frame = capture.read()
	capture.release()
	if has_frame:
		return frame
	return None


def count_video_frame_total(video_path : str) -> int:
	capture = cv2.VideoCapture(video_path)
	video_frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
	capture.release()
	return video_frame_total


def normalize_frame(frame : Frame) -> Frame:
	return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
