import cv2

from facefusion.types import VideoPoolSet

VIDEO_POOL_SET : VideoPoolSet =\
{
	'capture': {},
	'writer': {}
}


def get_video_capture(video_path : str) -> cv2.VideoCapture:
	if video_path not in VIDEO_POOL_SET.get('capture'):
		video_capture = cv2.VideoCapture(video_path)

		if video_capture.isOpened():
			VIDEO_POOL_SET['capture'][video_path] = video_capture

	return VIDEO_POOL_SET.get('capture').get(video_path)


def get_video_writer(video_path : str) -> cv2.VideoWriter:
	if video_path not in VIDEO_POOL_SET.get('writer'):
		video_writer = cv2.VideoWriter()

		if video_writer.isOpened():
			VIDEO_POOL_SET['writer'][video_path] = video_writer

	return VIDEO_POOL_SET.get('writer').get(video_path)


def clear_video_pool() -> None:
	for video_capture in VIDEO_POOL_SET.get('capture').values():
		video_capture.release()

	for video_writer in VIDEO_POOL_SET.get('writer').values():
		video_writer.release()

	VIDEO_POOL_SET['capture'].clear()
	VIDEO_POOL_SET['writer'].clear()
