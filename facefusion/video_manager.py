import cv2

from facefusion.types import VideoPoolSet

VIDEO_POOL_SET : VideoPoolSet =\
{
	'capture': {},
	'writer': {}
}


def get_video_capture(video_path : str) -> cv2.VideoCapture:
	if video_path not in VIDEO_POOL_SET.get('capture'):
		VIDEO_POOL_SET['capture'][video_path] = cv2.VideoCapture(video_path)

	return VIDEO_POOL_SET.get('capture').get(video_path)


def get_video_writer(video_path : str) -> cv2.VideoWriter:
	if video_path not in VIDEO_POOL_SET.get('writer'):
		VIDEO_POOL_SET['writer'][video_path] = cv2.VideoWriter()

	return VIDEO_POOL_SET.get('writer').get(video_path)


def clear_video_pool() -> None:
	for video_capture in VIDEO_POOL_SET.get('capture').values():
		video_capture.release()

	for video_writer in VIDEO_POOL_SET.get('writer').values():
		video_writer.release()

	VIDEO_POOL_SET['capture'].clear()
	VIDEO_POOL_SET['writer'].clear()
