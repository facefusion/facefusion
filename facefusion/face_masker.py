from configparser import Interpolation
from typing import Any, Dict, List
from cv2.typing import Size
from functools import lru_cache
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.typing import Frame, Mask, ModelValue, Padding, FaceMaskRegion
from facefusion.filesystem import resolve_relative_path
from facefusion.download import conditional_download

FACE_OCCLUDER = None
FACE_PARSER = None
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : Dict[str, ModelValue] =\
{
	'occluder':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/occluder.onnx',
		'path': resolve_relative_path('../.assets/models/occluder.onnx')
	},
	'parser':
	{
		'url': 'https://filebin.net/c090an8lf7ppgh91/parser.onnx',
		'path': resolve_relative_path('../.assets/models/parser.onnx')
	}
}
FACE_MASK_REGION_MAP : Dict[FaceMaskRegion, int] =\
{
    "skin": 1,
    "left-eyebrow": 2,
    "right-eyebrow": 3,
    "left-eye": 4,
    "right-eye": 5,
    "eye-glasses": 6,
    "left-ear": 7,
    "right-ear": 8,
    "earring": 9,
    "nose": 10,
    "mouth": 11,
    "upper-lip": 12,
    "lower-lip": 13,
    "neck": 14,
    "necklace": 15,
    "cloth": 16,
    "hair": 17,
    "hat": 18,
	"occlusion": 19
}


def get_face_occluder() -> Any:
	global FACE_OCCLUDER

	with THREAD_LOCK:
		if FACE_OCCLUDER is None:
			model_path = MODELS.get('occluder').get('path')
			FACE_OCCLUDER = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FACE_OCCLUDER


def get_face_parser() -> Any:
	global FACE_PARSER

	with THREAD_LOCK:
		if FACE_PARSER is None:
			model_path = MODELS.get('parser').get('path')
			FACE_PARSER = onnxruntime.InferenceSession(model_path, providers = facefusion.globals.execution_providers)
	return FACE_PARSER


def clear_masks() -> None:
	global FACE_OCCLUDER
	global FACE_PARSER

	FACE_OCCLUDER = None
	FACE_PARSER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_urls =\
		[
			MODELS.get('occluder').get('url'),
			MODELS.get('parser').get('url'),
		]
		conditional_download(download_directory_path, model_urls)
	return True


def merge_masks(masks : List[Mask]) -> Mask:
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
	occluder_mask = 1 - (create_parser_mask(crop_frame, ['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'eye-glasses', 'nose', 'upper-lip', 'lower-lip', 'mouth']) - occluder_mask)
	return occluder_mask


def create_parser_mask(crop_frame : Frame, face_mask_regions : List[FaceMaskRegion]) -> Mask:
	face_parser = get_face_parser()
	prepare_frame = cv2.resize(crop_frame, (512, 512))
	prepare_frame = numpy.expand_dims(prepare_frame, axis = 0).astype(numpy.float32)[:, :, ::-1] / 127.5 - 1
	prepare_frame = prepare_frame.transpose(0, 3, 1, 2)
	parser_output = face_parser.run(None,
	{
		face_parser.get_inputs()[0].name: prepare_frame
  	})[0][0]
	parser_mask = numpy.isin(parser_output.argmax(0), [FACE_MASK_REGION_MAP[region] for region in face_mask_regions if region != 'occlusion'])
	parser_mask = (cv2.GaussianBlur(parser_mask.astype(numpy.float32).clip(0, 1), (0, 0), 5).clip(0.5, 1) - 0.5) * 2
	parser_mask = cv2.resize(parser_mask, crop_frame.shape[:2][::-1])
	return parser_mask
