from functools import lru_cache
from time import sleep
from typing import Dict, List, Optional

import cv2
import numpy
from cv2.typing import Size

from facefusion import process_manager, state_manager
from facefusion.execution import create_inference_pool
from facefusion.filesystem import resolve_relative_path
from facefusion.source_helper import conditional_download_hashes, conditional_download_sources
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.typing import FaceLandmark68, FaceMaskRegion, InferencePool, Mask, ModelOptions, ModelSet, Padding, VisionFrame

INFERENCE_POOL : Optional[InferencePool] = None
MODEL_SET : ModelSet =\
{
	'face_masker':
	{
		'hashes':
		{
			'face_occluder':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/dfl_xseg.hash',
				'path': resolve_relative_path('../.assets/models/dfl_xseg.hash')
			},
			'face_parser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/resnet_34.hash',
				'path': resolve_relative_path('../.assets/models/resnet_34.hash')
			}
		},
		'sources':
		{
			'face_occluder':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/dfl_xseg.onnx',
				'path': resolve_relative_path('../.assets/models/dfl_xseg.onnx')
			},
			'face_parser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/resnet_34.onnx',
				'path': resolve_relative_path('../.assets/models/resnet_34.onnx')
			}
		}
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


def get_inference_pool() -> InferencePool:
	global INFERENCE_POOL

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOL is None:
			model_sources = get_model_options().get('sources')
			INFERENCE_POOL = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
		return INFERENCE_POOL


def clear_inference_pool() -> None:
	global INFERENCE_POOL

	INFERENCE_POOL = None


def get_model_options() -> ModelOptions:
	return MODEL_SET.get('face_masker')


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = get_model_options().get('hashes')
	model_sources = get_model_options().get('sources')

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


@lru_cache(maxsize = None)
def create_static_box_mask(crop_size : Size, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	blur_amount = int(crop_size[0] * 0.5 * face_mask_blur)
	blur_area = max(blur_amount // 2, 1)
	box_mask : Mask = numpy.ones(crop_size).astype(numpy.float32)
	box_mask[:max(blur_area, int(crop_size[1] * face_mask_padding[0] / 100)), :] = 0
	box_mask[-max(blur_area, int(crop_size[1] * face_mask_padding[2] / 100)):, :] = 0
	box_mask[:, :max(blur_area, int(crop_size[0] * face_mask_padding[3] / 100))] = 0
	box_mask[:, -max(blur_area, int(crop_size[0] * face_mask_padding[1] / 100)):] = 0
	if blur_amount > 0:
		box_mask = cv2.GaussianBlur(box_mask, (0, 0), blur_amount * 0.25)
	return box_mask


def create_occlusion_mask(crop_vision_frame : VisionFrame) -> Mask:
	face_occluder = get_inference_pool().get('face_occluder')
	prepare_vision_frame = cv2.resize(crop_vision_frame, face_occluder.get_inputs()[0].shape[1:3][::-1])
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0).astype(numpy.float32) / 255
	prepare_vision_frame = prepare_vision_frame.transpose(0, 1, 2, 3)

	with conditional_thread_semaphore():
		occlusion_mask : Mask = face_occluder.run(None,
		{
			face_occluder.get_inputs()[0].name: prepare_vision_frame
		})[0][0]

	occlusion_mask = occlusion_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occlusion_mask = cv2.resize(occlusion_mask, crop_vision_frame.shape[:2][::-1])
	occlusion_mask = (cv2.GaussianBlur(occlusion_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return occlusion_mask


def create_region_mask(crop_vision_frame : VisionFrame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	face_parser = get_inference_pool().get('face_parser')
	prepare_vision_frame = cv2.resize(crop_vision_frame, (512, 512))
	prepare_vision_frame = prepare_vision_frame[:, :, ::-1].astype(numpy.float32) / 255
	prepare_vision_frame = numpy.subtract(prepare_vision_frame, numpy.array([ 0.485, 0.456, 0.406 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.divide(prepare_vision_frame, numpy.array([ 0.229, 0.224, 0.225 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0)
	prepare_vision_frame = prepare_vision_frame.transpose(0, 3, 1, 2)

	with conditional_thread_semaphore():
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
	mouth_mask = cv2.fillConvexPoly(mouth_mask, convex_hull, 1.0) #type:ignore[call-overload]
	mouth_mask = cv2.erode(mouth_mask.clip(0, 1), numpy.ones((21, 3)))
	mouth_mask = cv2.GaussianBlur(mouth_mask, (0, 0), sigmaX = 1, sigmaY = 15)
	return mouth_mask


def create_face_mask(crop_vision_frame : VisionFrame) -> Mask:
	face_regions : List[FaceMaskRegion] = [ 'skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip' ]
	return create_region_mask(crop_vision_frame, face_regions)
