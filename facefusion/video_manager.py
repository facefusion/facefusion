import os
import time
import threading
import cv2

from facefusion import logger
from facefusion.types import VideoPoolSet

VIDEO_POOL_SET : VideoPoolSet =\
{
	'capture': {},
	'writer': {}
}

mutex_video_capture = threading.Lock()

def get_video_capture(video_path : str, retry : int = 100) -> cv2.VideoCapture:
	mutex_video_capture.acquire() # lock
	if video_path in VIDEO_POOL_SET.get('capture'):
		mutex_video_capture.release() # unlock
		return VIDEO_POOL_SET.get('capture').get(video_path)
	#
	counter = 0
	while True:
		try:
			video_capture = cv2.VideoCapture(video_path)
			if not video_capture.isOpened():
				raise RuntimeError('video capture not opened')
			VIDEO_POOL_SET['capture'][video_path] = video_capture
			mutex_video_capture.release() # unlock
			logger.info(f'video file loaded: {os.path.basename(video_path)}', __name__)
			return VIDEO_POOL_SET.get('capture').get(video_path)
		except Exception as e:
			if counter > retry:
				mutex_video_capture.release() # unlock
				raise e
			#
			logger.warn(f'retry {counter} of {retry}: {str(e)}', __name__)
			counter += 1
			time.sleep(10)

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
