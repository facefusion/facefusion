from functools import lru_cache
from typing import List, Tuple

import cv2
import numpy

import facefusion.choices
from facefusion import inference_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import DownloadScope, DownloadSet, FaceLandmark68, FaceMaskArea, FaceMaskRegion, InferencePool, Mask, ModelSet, Padding, VisionFrame


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'xseg_1':
		{
			'hashes':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.1.0', 'xseg_1.hash'),
					'path': resolve_relative_path('../.assets/models/xseg_1.hash')
				}
			},
			'sources':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.1.0', 'xseg_1.onnx'),
					'path': resolve_relative_path('../.assets/models/xseg_1.onnx')
				}
			},
			'size': (256, 256)
		},
		'xseg_2':
		{
			'hashes':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.1.0', 'xseg_2.hash'),
					'path': resolve_relative_path('../.assets/models/xseg_2.hash')
				}
			},
			'sources':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.1.0', 'xseg_2.onnx'),
					'path': resolve_relative_path('../.assets/models/xseg_2.onnx')
				}
			},
			'size': (256, 256)
		},
		'xseg_3':
		{
			'hashes':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.2.0', 'xseg_3.hash'),
					'path': resolve_relative_path('../.assets/models/xseg_3.hash')
				}
			},
			'sources':
			{
				'face_occluder':
				{
					'url': resolve_download_url('models-3.2.0', 'xseg_3.onnx'),
					'path': resolve_relative_path('../.assets/models/xseg_3.onnx')
				}
			},
			'size': (256, 256)
		},
		'bisenet_resnet_18':
		{
			'hashes':
			{
				'face_parser':
				{
					'url': resolve_download_url('models-3.1.0', 'bisenet_resnet_18.hash'),
					'path': resolve_relative_path('../.assets/models/bisenet_resnet_18.hash')
				}
			},
			'sources':
			{
				'face_parser':
				{
					'url': resolve_download_url('models-3.1.0', 'bisenet_resnet_18.onnx'),
					'path': resolve_relative_path('../.assets/models/bisenet_resnet_18.onnx')
				}
			},
			'size': (512, 512)
		},
		'bisenet_resnet_34':
		{
			'hashes':
			{
				'face_parser':
				{
					'url': resolve_download_url('models-3.0.0', 'bisenet_resnet_34.hash'),
					'path': resolve_relative_path('../.assets/models/bisenet_resnet_34.hash')
				}
			},
			'sources':
			{
				'face_parser':
				{
					'url': resolve_download_url('models-3.0.0', 'bisenet_resnet_34.onnx'),
					'path': resolve_relative_path('../.assets/models/bisenet_resnet_34.onnx')
				}
			},
			'size': (512, 512)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('face_occluder_model'), state_manager.get_item('face_parser_model') ]
	_, model_source_set = collect_model_downloads()

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('face_occluder_model'), state_manager.get_item('face_parser_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_set = create_static_model_set('full')
	model_hash_set = {}
	model_source_set = {}

	for face_occluder_model in [ 'xseg_1', 'xseg_2', 'xseg_3' ]:
		if state_manager.get_item('face_occluder_model') == face_occluder_model:
			model_hash_set[face_occluder_model] = model_set.get(face_occluder_model).get('hashes').get('face_occluder')
			model_source_set[face_occluder_model] = model_set.get(face_occluder_model).get('sources').get('face_occluder')

	for face_parser_model in [ 'bisenet_resnet_18', 'bisenet_resnet_34' ]:
		if state_manager.get_item('face_parser_model') == face_parser_model:
			model_hash_set[face_parser_model] = model_set.get(face_parser_model).get('hashes').get('face_parser')
			model_source_set[face_parser_model] = model_set.get(face_parser_model).get('sources').get('face_parser')

	return model_hash_set, model_source_set


def pre_check() -> bool:
	model_hash_set, model_source_set = collect_model_downloads()

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def create_box_mask(crop_vision_frame : VisionFrame, face_mask_blur : float, face_mask_padding : Padding) -> Mask:
	crop_size = crop_vision_frame.shape[:2][::-1]
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
	model_name = state_manager.get_item('face_occluder_model')
	model_size = create_static_model_set('full').get(model_name).get('size')
	prepare_vision_frame = cv2.resize(crop_vision_frame, model_size)
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0).astype(numpy.float32) / 255.0
	prepare_vision_frame = prepare_vision_frame.transpose(0, 1, 2, 3)
	occlusion_mask = forward_occlude_face(prepare_vision_frame)
	occlusion_mask = occlusion_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occlusion_mask = cv2.resize(occlusion_mask, crop_vision_frame.shape[:2][::-1])
	occlusion_mask = (cv2.GaussianBlur(occlusion_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return occlusion_mask


def create_area_mask(crop_vision_frame : VisionFrame, face_landmark_68 : FaceLandmark68, face_mask_areas : List[FaceMaskArea]) -> Mask:
	crop_size = crop_vision_frame.shape[:2][::-1]
	landmark_points = []

	for face_mask_area in face_mask_areas:
		if face_mask_area in facefusion.choices.face_mask_area_set:
			landmark_points.extend(facefusion.choices.face_mask_area_set.get(face_mask_area))

	convex_hull = cv2.convexHull(face_landmark_68[landmark_points].astype(numpy.int32))
	area_mask = numpy.zeros(crop_size).astype(numpy.float32)
	cv2.fillConvexPoly(area_mask, convex_hull, 1.0) # type: ignore[call-overload]
	area_mask = (cv2.GaussianBlur(area_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return area_mask


def create_region_mask(crop_vision_frame : VisionFrame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	model_name = state_manager.get_item('face_parser_model')
	model_size = create_static_model_set('full').get(model_name).get('size')
	prepare_vision_frame = cv2.resize(crop_vision_frame, model_size)
	prepare_vision_frame = prepare_vision_frame[:, :, ::-1].astype(numpy.float32) / 255.0
	prepare_vision_frame = numpy.subtract(prepare_vision_frame, numpy.array([ 0.485, 0.456, 0.406 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.divide(prepare_vision_frame, numpy.array([ 0.229, 0.224, 0.225 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0)
	prepare_vision_frame = prepare_vision_frame.transpose(0, 3, 1, 2)
	region_mask = forward_parse_face(prepare_vision_frame)
	region_mask = numpy.isin(region_mask.argmax(0), [ facefusion.choices.face_mask_region_set.get(face_mask_region) for face_mask_region in face_mask_regions ])
	region_mask = cv2.resize(region_mask.astype(numpy.float32), crop_vision_frame.shape[:2][::-1])
	region_mask = (cv2.GaussianBlur(region_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return region_mask


def forward_occlude_face(prepare_vision_frame : VisionFrame) -> Mask:
	model_name = state_manager.get_item('face_occluder_model')
	face_occluder = get_inference_pool().get(model_name)

	with conditional_thread_semaphore():
		occlusion_mask : Mask = face_occluder.run(None,
		{
			'input': prepare_vision_frame
		})[0][0]

	return occlusion_mask


def forward_parse_face(prepare_vision_frame : VisionFrame) -> Mask:
	model_name = state_manager.get_item('face_parser_model')
	face_parser = get_inference_pool().get(model_name)

	with conditional_thread_semaphore():
		region_mask : Mask = face_parser.run(None,
		{
			'input': prepare_vision_frame
		})[0][0]

	return region_mask
