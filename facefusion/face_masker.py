from typing import Any, Dict
from functools import lru_cache
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from cv2.typing import Size
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
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = [ 'CPUExecutionProvider' ])
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


def create_mask(crop_frame : Frame, face_mask_type : FaceMaskType, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	masks = []
	if 'box' in face_mask_type:
		masks.append(create_static_box_mask(crop_frame.shape[:2][::-1], face_mask_blur, face_mask_padding))
	if 'occluder' in face_mask_type:
		masks.append(create_face_occluder_mask(crop_frame, face_mask_blur))
	return numpy.minimum.reduce(masks).clip(0, 1)


def create_face_occluder_mask(crop_frame : Frame, face_mask_blur : float) -> Mask:
	face_occluder = get_face_occluder()
	occluder_inputs = face_occluder.get_inputs()
	crop_frame_resized = cv2.resize(crop_frame, occluder_inputs[0].shape[1:3][::-1])
	crop_frame_resized = numpy.expand_dims(crop_frame_resized, axis=0).astype(numpy.float32) / 255
	crop_frame_resized = crop_frame_resized.transpose(0, 1, 2, 3)
	occluder_mask = face_occluder.run(None, {occluder_inputs[0].name: crop_frame_resized})[0][0]
	occluder_mask = occluder_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occluder_mask = cv2.resize(occluder_mask, crop_frame.shape[:2][::-1])
	occluder_mask = cv2.GaussianBlur(occluder_mask, (0, 0), max(int(crop_frame.shape[1] * 0.125 * face_mask_blur), 1))
	return occluder_mask


@lru_cache(maxsize = None)
def create_static_box_mask(mask_size : Size, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	mask_frame = numpy.ones(mask_size, numpy.float32)
	blur_amount = int(mask_size[0] * 0.5 * face_mask_blur)
	blur_area = max(blur_amount // 2, 1)
	mask_frame[:max(blur_area, int(mask_size[1] * face_mask_padding[0] / 100)), :] = 0
	mask_frame[-max(blur_area, int(mask_size[1] * face_mask_padding[2] / 100)):, :] = 0
	mask_frame[:, :max(blur_area, int(mask_size[0] * face_mask_padding[3] / 100))] = 0
	mask_frame[:, -max(blur_area, int(mask_size[0] * face_mask_padding[1] / 100)):] = 0
	if blur_amount > 0:
		mask_frame = cv2.GaussianBlur(mask_frame, (0, 0), blur_amount * 0.25)
	return mask_frame
