from typing import Any, Dict, List
from cv2.typing import Size
from functools import lru_cache
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.typing import FaceMaskType, Frame, Mask, ModelValue, Padding
from facefusion.utilities import resolve_relative_path, conditional_download

FACE_OCCLUDER = None
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : Dict[str, ModelValue] =\
{
	'occluder':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/occluder.onnx',
		'path': resolve_relative_path('../.assets/models/occluder.onnx')
	}
}


def get_face_occluder() -> Any:
	global FACE_OCCLUDER

	with THREAD_LOCK:
		if FACE_OCCLUDER is None:
			model_path = MODELS.get('occluder').get('path')
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FACE_OCCLUDER


def clear_face_occluder() -> None:
	global FACE_OCCLUDER

	FACE_OCCLUDER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_url = MODELS.get('occluder').get('url')
		conditional_download(download_directory_path, [ model_url ])
	return True


def create_mask(crop_frame : Frame, face_mask_types : List[FaceMaskType], face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	masks = []
	if 'box' in face_mask_types:
		masks.append(create_static_box_mask(crop_frame.shape[:2][::-1], face_mask_blur, face_mask_padding))
	if 'occluder' in face_mask_types:
		masks.append(create_occluder_mask(crop_frame))
	return numpy.minimum.reduce(masks).clip(0, 1)


@lru_cache(maxsize = None)
def create_static_box_mask(mask_size : Size, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	blur_amount = int(mask_size[0] * 0.5 * face_mask_blur)
	blur_area = max(blur_amount // 2, 1)
	box_mask = numpy.ones(mask_size, numpy.float32)
	box_mask[:max(blur_area, int(mask_size[1] * face_mask_padding[0] / 100)), :] = 0
	box_mask[-max(blur_area, int(mask_size[1] * face_mask_padding[2] / 100)):, :] = 0
	box_mask[:, :max(blur_area, int(mask_size[0] * face_mask_padding[3] / 100))] = 0
	box_mask[:, -max(blur_area, int(mask_size[0] * face_mask_padding[1] / 100)):] = 0
	if blur_amount > 0:
		box_mask = cv2.GaussianBlur(box_mask, (0, 0), blur_amount * 0.25)
	return box_mask


def create_occluder_mask(crop_frame : Frame) -> Mask:
	face_occluder = get_face_occluder()
	prepare_frame = cv2.resize(crop_frame, face_occluder.get_inputs()[0].shape[1:3][::-1])
	prepare_frame = numpy.expand_dims(prepare_frame, axis = 0).astype(numpy.float32) / 255
	prepare_frame = prepare_frame.transpose(0, 1, 2, 3)
	occluder_mask = face_occluder.run(None,
	{
		face_occluder.get_inputs()[0].name: prepare_frame
	})[0][0]
	occluder_mask = occluder_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occluder_mask = cv2.resize(occluder_mask, crop_frame.shape[:2][::-1])
	return occluder_mask
