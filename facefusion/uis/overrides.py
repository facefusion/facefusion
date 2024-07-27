import base64
from typing import Any

import cv2
import numpy
from numpy._typing import NDArray


def encode_array_to_base64(array : NDArray[Any]) -> str:
	_, buffer = cv2.imencode('.jpg', array[:, :, ::-1])
	return 'data:image/jpeg;base64,' + base64.b64encode(buffer.tobytes()).decode('utf-8')


def encode_pil_to_base64(image : Any) -> str:
	return encode_array_to_base64(numpy.asarray(image)[:, :, ::-1])
