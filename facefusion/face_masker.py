from typing import Any, Dict
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.typing import Frame, ModelValue
from facefusion.utilities import resolve_relative_path, conditional_download

FACE_OCCLUDER = None
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : Dict[str, ModelValue] =\
{
	'face_occluder':
	{
		'url': 'https://filebin.net/fm154w5a1dvqszm7/face_occluder.onnx',
		'path': resolve_relative_path('../.assets/models/face_occluder.onnx')
	}
}


def get_face_occluder() -> Any:
	global FACE_OCCLUDER

	with THREAD_LOCK:
		if FACE_OCCLUDER is None:
			model_path = MODELS.get('face_occluder').get('path')
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = [ 'CPUExecutionProvider' ])
	return FACE_OCCLUDER


def clear_face_occluder() -> None:
	global FACE_OCCLUDER

	FACE_OCCLUDER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_url = MODELS.get('face_occluder').get('url')
		conditional_download(download_directory_path, [ model_url ])
	return True


def create_face_occluder_mask(crop_frame : Frame) -> Frame:
	global FACE_OCCLUDER

	FACE_OCCLUDER = get_face_occluder()
	crop_frame_size = crop_frame.shape[:2][::-1]
	occluder_inputs = FACE_OCCLUDER.get_inputs()
	crop_frame_resized = cv2.resize(crop_frame, occluder_inputs[0].shape[1:3][::-1])
	crop_frame_resized = numpy.expand_dims(crop_frame_resized, axis=0).astype(numpy.float32) / 255
	crop_frame_resized = crop_frame_resized.transpose(0, 1, 2, 3)
	face_occluder_mask = FACE_OCCLUDER.run(None, {occluder_inputs[0].name: crop_frame_resized})[0][0]
	face_occluder_mask = face_occluder_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	face_occluder_mask = cv2.resize(face_occluder_mask, crop_frame_size)
	return face_occluder_mask
