import cv2

from facefusion.types import VideoPoolSet

VIDEO_POOL_SET : VideoPoolSet = {}


def get_video_capture(video_path : str) -> cv2.VideoCapture:
	if video_path not in VIDEO_POOL_SET:
		VIDEO_POOL_SET[video_path] = cv2.VideoCapture(video_path)

	return VIDEO_POOL_SET.get(video_path)


def clear_video_pool() -> None:
	for video_capture in VIDEO_POOL_SET.values():
		video_capture.release()

	VIDEO_POOL_SET.clear()
