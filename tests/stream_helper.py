import cv2
import numpy


def create_test_frame_bytes(width : int, height : int) -> bytes:
	vision_frame = numpy.zeros((height, width, 3), dtype = numpy.uint8)
	is_success, image_buffer = cv2.imencode('.jpg', vision_frame)

	if is_success:
		return image_buffer.tobytes()
	return b''
