from typing import List, Optional

import cv2

from facefusion.common_helper import is_windows
from facefusion.types import WebcamPoolSet

WEBCAM_POOL_SET : WebcamPoolSet =\
{
	'capture': {}
}


def get_webcam_capture(device_id : int) -> Optional[cv2.VideoCapture]:
	if device_id not in WEBCAM_POOL_SET.get('capture'):
		if is_windows():
			WEBCAM_POOL_SET['capture'][device_id] = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
		else:
			WEBCAM_POOL_SET['capture'][device_id] = cv2.VideoCapture(device_id)

	return WEBCAM_POOL_SET.get('capture').get(device_id)


def clear_webcam_pool() -> None:
	for webcam_capture in WEBCAM_POOL_SET.get('capture').values():
		webcam_capture.release()

	WEBCAM_POOL_SET['capture'].clear()


def detect_available_webcam_ids(id_start : int, id_end : int) -> List[int]:
	available_device_ids = []

	for device_id in range(id_start, id_end):
		cv2.setLogLevel(0)
		webcam_capture = get_webcam_capture(device_id)
		cv2.setLogLevel(3)

		if webcam_capture and webcam_capture.isOpened():
			available_device_ids.append(device_id)

	clear_webcam_pool()
	return available_device_ids
