from typing import Any, Dict, List
from cv2.typing import Size
from functools import lru_cache
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.typing import Frame, Mask, Padding, FaceMaskRegion, ModelSet
from facefusion.filesystem import resolve_relative_path
from facefusion.download import conditional_download

FACE_OCCLUDER = None
FACE_PARSER = None
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : ModelSet =\
{
	'face_occluder':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/face_occluder.onnx',
		'path': resolve_relative_path('../.assets/models/face_occluder.onnx')
	},
	'face_parser':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/face_parser.onnx',
		'path': resolve_relative_path('../.assets/models/face_parser.onnx')
	}
}
FACE_MASK_REGIONS : Dict[FaceMaskRegion, int] =\
{
	'skin': 1,
	'left-eyebrow': 2,
	'right-eyebrow': 3,
	'left-eye': 4,
	'right-eye': 5,
	'eye-glasses': 6,
	'nose': 10,
	'mouth': 11,
	'upper-lip': 12,
	'lower-lip': 13
}


def get_face_occluder() -> Any:
	global FACE_OCCLUDER

	with THREAD_LOCK:
		if FACE_OCCLUDER is None:
			model_path = MODELS.get('face_occluder').get('path')
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FACE_OCCLUDER


def get_face_parser() -> Any:
	global FACE_PARSER

	with THREAD_LOCK:
		if FACE_PARSER is None:
			model_path = MODELS.get('face_parser').get('path')
			FACE_PARSER = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FACE_PARSER


def clear_face_occluder() -> None:
	global FACE_OCCLUDER

	FACE_OCCLUDER = None


def clear_face_parser() -> None:
	global FACE_PARSER

	FACE_PARSER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_urls =\
		[
			MODELS.get('face_occluder').get('url'),
			MODELS.get('face_parser').get('url'),
		]
		conditional_download(download_directory_path, model_urls)
	return True


@lru_cache(maxsize = None)
def create_static_box_mask(crop_size : Size, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	blur_amount = int(crop_size[0] * 0.5 * face_mask_blur)
	blur_area = max(blur_amount // 2, 1)
	box_mask = numpy.ones(crop_size, numpy.float32)
	box_mask[:max(blur_area, int(crop_size[1] * face_mask_padding[0] / 100)), :] = 0
	box_mask[-max(blur_area, int(crop_size[1] * face_mask_padding[2] / 100)):, :] = 0
	box_mask[:, :max(blur_area, int(crop_size[0] * face_mask_padding[3] / 100))] = 0
	box_mask[:, -max(blur_area, int(crop_size[0] * face_mask_padding[1] / 100)):] = 0
	if blur_amount > 0:
		box_mask = cv2.GaussianBlur(box_mask, (0, 0), blur_amount * 0.25)
	return box_mask


def create_occlusion_mask(crop_frame : Frame) -> Mask:
	face_occluder = get_face_occluder()
	prepare_frame = cv2.resize(crop_frame, face_occluder.get_inputs()[0].shape[1:3][::-1])
	prepare_frame = numpy.expand_dims(prepare_frame, axis = 0).astype(numpy.float32) / 255
	prepare_frame = prepare_frame.transpose(0, 1, 2, 3)
	occlusion_mask = face_occluder.run(None,
	{
		face_occluder.get_inputs()[0].name: prepare_frame
	})[0][0]
	occlusion_mask = occlusion_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occlusion_mask = cv2.resize(occlusion_mask, crop_frame.shape[:2][::-1])
	return occlusion_mask


def create_region_mask(crop_frame : Frame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	face_parser = get_face_parser()
	prepare_frame = cv2.flip(cv2.resize(crop_frame, (512, 512)), 1)
	prepare_frame = numpy.expand_dims(prepare_frame, axis = 0).astype(numpy.float32)[:, :, ::-1] / 127.5 - 1
	prepare_frame = prepare_frame.transpose(0, 3, 1, 2)
	region_mask = face_parser.run(None,
	{
		face_parser.get_inputs()[0].name: prepare_frame
	})[0][0]
	region_mask = numpy.isin(region_mask.argmax(0), [ FACE_MASK_REGIONS[region] for region in face_mask_regions ])
	region_mask = cv2.resize(region_mask.astype(numpy.float32), crop_frame.shape[:2][::-1])
	return region_mask
