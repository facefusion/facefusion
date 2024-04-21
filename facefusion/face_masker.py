from typing import Any, Dict, List
from functools import lru_cache
from time import sleep
import cv2
from cv2.typing import Size
import numpy
import onnxruntime

import facefusion.globals
from facefusion import process_manager
from facefusion.thread_helper import thread_lock, conditional_thread_semaphore
from facefusion.typing import FaceLandmark68, VisionFrame, Mask, Padding, FaceMaskRegion, ModelSet
from facefusion.execution import apply_execution_provider_options
from facefusion.filesystem import resolve_relative_path, is_file
from facefusion.download import conditional_download

FACE_OCCLUDER = None
FACE_PARSER = None
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
	'glasses': 6,
	'nose': 10,
	'mouth': 11,
	'upper-lip': 12,
	'lower-lip': 13
}


def get_face_occluder() -> Any:
	global FACE_OCCLUDER

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if FACE_OCCLUDER is None:
			model_path = MODELS.get('face_occluder').get('path')
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_providers))
	return FACE_OCCLUDER


def get_face_parser() -> Any:
	global FACE_PARSER

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if FACE_PARSER is None:
			model_path = MODELS.get('face_parser').get('path')
			FACE_PARSER = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_providers))
	return FACE_PARSER


def clear_face_occluder() -> None:
	global FACE_OCCLUDER

	FACE_OCCLUDER = None


def clear_face_parser() -> None:
	global FACE_PARSER

	FACE_PARSER = None


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_urls =\
	[
		MODELS.get('face_occluder').get('url'),
		MODELS.get('face_parser').get('url')
	]
	model_paths =\
	[
		MODELS.get('face_occluder').get('path'),
		MODELS.get('face_parser').get('path')
	]

	if not facefusion.globals.skip_download:
		process_manager.check()
		conditional_download(download_directory_path, model_urls)
		process_manager.end()
	return all(is_file(model_path) for model_path in model_paths)


@lru_cache(maxsize = None)
def create_static_box_mask(crop_size : Size, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	blur_amount = int(crop_size[0] * 0.5 * face_mask_blur)
	blur_area = max(blur_amount // 2, 1)
	box_mask : Mask = numpy.ones(crop_size, numpy.float32)
	box_mask[:max(blur_area, int(crop_size[1] * face_mask_padding[0] / 100)), :] = 0
	box_mask[-max(blur_area, int(crop_size[1] * face_mask_padding[2] / 100)):, :] = 0
	box_mask[:, :max(blur_area, int(crop_size[0] * face_mask_padding[3] / 100))] = 0
	box_mask[:, -max(blur_area, int(crop_size[0] * face_mask_padding[1] / 100)):] = 0
	if blur_amount > 0:
		box_mask = cv2.GaussianBlur(box_mask, (0, 0), blur_amount * 0.25)
	return box_mask


def create_occlusion_mask(crop_vision_frame : VisionFrame) -> Mask:
	face_occluder = get_face_occluder()
	prepare_vision_frame = cv2.resize(crop_vision_frame, face_occluder.get_inputs()[0].shape[1:3][::-1])
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0).astype(numpy.float32) / 255
	prepare_vision_frame = prepare_vision_frame.transpose(0, 1, 2, 3)
	with conditional_thread_semaphore(facefusion.globals.execution_providers):
		occlusion_mask : Mask = face_occluder.run(None,
		{
			face_occluder.get_inputs()[0].name: prepare_vision_frame
		})[0][0]
	occlusion_mask = occlusion_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occlusion_mask = cv2.resize(occlusion_mask, crop_vision_frame.shape[:2][::-1])
	occlusion_mask = (cv2.GaussianBlur(occlusion_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return occlusion_mask


def create_region_mask(crop_vision_frame : VisionFrame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	face_parser = get_face_parser()
	prepare_vision_frame = cv2.flip(cv2.resize(crop_vision_frame, (512, 512)), 1)
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0).astype(numpy.float32)[:, :, ::-1] / 127.5 - 1
	prepare_vision_frame = prepare_vision_frame.transpose(0, 3, 1, 2)
	with conditional_thread_semaphore(facefusion.globals.execution_providers):
		region_mask : Mask = face_parser.run(None,
		{
			face_parser.get_inputs()[0].name: prepare_vision_frame
		})[0][0]
	region_mask = numpy.isin(region_mask.argmax(0), [ FACE_MASK_REGIONS[region] for region in face_mask_regions ])
	region_mask = cv2.resize(region_mask.astype(numpy.float32), crop_vision_frame.shape[:2][::-1])
	region_mask = (cv2.GaussianBlur(region_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return region_mask


def create_mouth_mask(face_landmark_68 : FaceLandmark68) -> Mask:
	convex_hull = cv2.convexHull(face_landmark_68[numpy.r_[3:14, 31:36]].astype(numpy.int32))
	mouth_mask : Mask = numpy.zeros((512, 512)).astype(numpy.float32)
	mouth_mask = cv2.fillConvexPoly(mouth_mask, convex_hull, 1.0)
	mouth_mask = cv2.erode(mouth_mask.clip(0, 1), numpy.ones((21, 3)))
	mouth_mask = cv2.GaussianBlur(mouth_mask, (0, 0), sigmaX = 1, sigmaY = 15)
	return mouth_mask
