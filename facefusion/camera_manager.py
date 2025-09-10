from typing import List

import cv2

from facefusion.types import CameraPoolSet

CAMERA_POOL_SET : CameraPoolSet =\
{
	'capture': {}
}


def get_local_camera_capture(camera_id : int) -> cv2.VideoCapture:
	camera_key = str(camera_id)

	if camera_key not in CAMERA_POOL_SET.get('capture'):
		camera_capture = cv2.VideoCapture(camera_id)

		if camera_capture.isOpened():
			CAMERA_POOL_SET['capture'][camera_key] = camera_capture

	return CAMERA_POOL_SET.get('capture').get(camera_key)


def get_remote_camera_capture(camera_url : str) -> cv2.VideoCapture:
	if camera_url not in CAMERA_POOL_SET.get('capture'):
		camera_capture = cv2.VideoCapture(camera_url)

		if camera_capture.isOpened():
			CAMERA_POOL_SET['capture'][camera_url] = camera_capture

	return CAMERA_POOL_SET.get('capture').get(camera_url)


def clear_camera_pool() -> None:
	for camera_capture in CAMERA_POOL_SET.get('capture').values():
		camera_capture.release()

	CAMERA_POOL_SET['capture'].clear()


def detect_local_camera_ids(id_start : int, id_end : int) -> List[int]:
	local_camera_ids = []

	for camera_id in range(id_start, id_end):
		cv2.setLogLevel(0)
		camera_capture = get_local_camera_capture(camera_id)
		cv2.setLogLevel(3)

		if camera_capture and camera_capture.isOpened():
			local_camera_ids.append(camera_id)

	return local_camera_ids
