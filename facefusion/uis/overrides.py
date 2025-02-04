from typing import Any
import cv2
import numpy
import base64


def encode_array_to_base64(array : numpy.ndarray[Any, Any]) -> str:
	buffer = cv2.imencode('.jpg', array[:, :, ::-1])[1]
	return 'data:image/jpeg;base64,' + base64.b64encode(buffer.tobytes()).decode('utf-8')


def encode_pil_to_base64(image : Any) -> str:
	return encode_array_to_base64(numpy.asarray(image)[:, :, ::-1])
