from functools import lru_cache
from typing import Dict, List, Tuple

import cv2
import numpy
from cv2.typing import Size

from facefusion import inference_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import DownloadSet, FaceLandmark68, FaceMaskRegion, InferencePool, Mask, ModelSet, Padding, VisionFrame

MODEL_SET : ModelSet =\
{
	'face_occluder':
	{
		'hashes':
		{
			'face_occluder':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/dfl_xseg.hash',
				'path': resolve_relative_path('../.assets/models/dfl_xseg.hash')
			}
		},
		'sources':
		{
			'face_occluder':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/dfl_xseg.onnx',
				'path': resolve_relative_path('../.assets/models/dfl_xseg.onnx')
			}
		},
		'size': (256, 256)
	},
	'face_parser':
	{
		'hashes':
		{
			'face_parser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/bisenet_resnet_34.hash',
				'path': resolve_relative_path('../.assets/models/bisenet_resnet_34.hash')
			}
		},
		'sources':
		{
			'face_parser':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/bisenet_resnet_34.onnx',
				'path': resolve_relative_path('../.assets/models/bisenet_resnet_34.onnx')
			}
		},
		'size': (512, 512)
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
	_, model_sources = collect_model_downloads()
	return inference_manager.get_inference_pool(__name__, model_sources)


def clear_inference_pool() -> None:
	inference_manager.clear_inference_pool(__name__)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_hashes =\
	{
		'face_occluder': MODEL_SET.get('face_occluder').get('hashes').get('face_occluder'),
		'face_parser': MODEL_SET.get('face_parser').get('hashes').get('face_parser')
	}
	model_sources =\
	{
		'face_occluder': MODEL_SET.get('face_occluder').get('sources').get('face_occluder'),
		'face_parser': MODEL_SET.get('face_parser').get('sources').get('face_parser')
	}
	return model_hashes, model_sources


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes, model_sources = collect_model_downloads()

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
	model_size = MODEL_SET.get('face_occluder').get('size')
	prepare_vision_frame = cv2.resize(crop_vision_frame, model_size)
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0).astype(numpy.float32) / 255
	prepare_vision_frame = prepare_vision_frame.transpose(0, 1, 2, 3)
	occlusion_mask = forward_occlude_face(prepare_vision_frame)
	occlusion_mask = occlusion_mask.transpose(0, 1, 2).clip(0, 1).astype(numpy.float32)
	occlusion_mask = cv2.resize(occlusion_mask, crop_vision_frame.shape[:2][::-1])
	occlusion_mask = (cv2.GaussianBlur(occlusion_mask.clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	return occlusion_mask


def create_region_mask(crop_vision_frame : VisionFrame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	model_size = MODEL_SET.get('face_parser').get('size')
	prepare_vision_frame = cv2.resize(crop_vision_frame, model_size)
	prepare_vision_frame = prepare_vision_frame[:, :, ::-1].astype(numpy.float32) / 255
	prepare_vision_frame = numpy.subtract(prepare_vision_frame, numpy.array([ 0.485, 0.456, 0.406 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.divide(prepare_vision_frame, numpy.array([ 0.229, 0.224, 0.225 ]).astype(numpy.float32))
	prepare_vision_frame = numpy.expand_dims(prepare_vision_frame, axis = 0)
	prepare_vision_frame = prepare_vision_frame.transpose(0, 3, 1, 2)
	region_mask = forward_parse_face(prepare_vision_frame)
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


def forward_occlude_face(prepare_vision_frame : VisionFrame) -> Mask:
	face_occluder = get_inference_pool().get('face_occluder')

	with conditional_thread_semaphore():
		occlusion_mask : Mask = face_occluder.run(None,
		{
			'input': prepare_vision_frame
		})[0][0]

	return occlusion_mask


def forward_parse_face(prepare_vision_frame : VisionFrame) -> Mask:
	face_parser = get_inference_pool().get('face_parser')

	with conditional_thread_semaphore():
		region_mask : Mask = face_parser.run(None,
		{
			'input': prepare_vision_frame
		})[0][0]

	return region_mask
