from typing import Any, List, Literal, Optional
from argparse import ArgumentParser
from cv2.typing import Size
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import config, process_manager, logger, wording
from facefusion.face_analyser import clear_face_analyser
from facefusion.content_analyser import clear_content_analyser
from facefusion.execution_helper import apply_execution_provider_options
from facefusion.typing import Face, VisionFrame, UpdateProcess, ProcessMode, ModelSet, OptionsWithModel, QueuePayload
from facefusion.common_helper import create_metavar
from facefusion.filesystem import is_file, resolve_relative_path
from facefusion.download import conditional_download, is_download_done
from facefusion.vision import read_image, read_static_image, write_image, merge_tile_frames, create_tile_frames
from facefusion.processors.frame.typings import FrameEnhancerInputs
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'lsdir_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIR/4xLSDIR_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIR_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'lsdir_compact_2_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIRCompact/Version2/4xLSDIRCompact2_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIRCompact2_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'lsdir_compact_3_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIRCompact/Version3/4xLSDIRCompact3_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIRCompact3_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'lsdir_plus_c_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIRplus/4xLSDIRplusC_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIRplusC_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'lsdir_plus_n_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIRplus/4xLSDIRplusN_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIRplusN_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'lsdir_plus_r_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xLSDIRplus/4xLSDIRplusR_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xLSDIRplusR_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'nomos8k_sc_4x':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xNomos8kSC/4xNomos8kSC_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xNomos8kSC_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'parimg_compact_x2':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/2xParimgCompact/2xParimgCompact_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/2xParimgCompact_fp32.onnx'),
		'size': (128, 8, 2)
	},
	'real_esrgan_128':
	{
		'url': 'https://huggingface.co/facefusion/next/resolve/main/realesrgan_128x128.onnx',
		'path': resolve_relative_path('../.assets/models/realesrgan_128x128.onnx'),
		'size': (128, 8, 2)
	},
	'real_esrgan_256':
	{
		'url': 'https://huggingface.co/facefusion/next/resolve/main/realesrgan_256x256.onnx',
		'path': resolve_relative_path('../.assets/models/realesrgan_256x256.onnx'),
		'size': (256, 8, 2)
	},
	'span_kendata_4x':
	{
		'url': 'https://github.com/terrainer/AI-Upscaling-Models/raw/main/4xSPANkendata/4xSPANkendata_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xSPANkendata_fp32.onnx'),
		'size': (256, 8, 2)
	}
}
OPTIONS : Optional[OptionsWithModel] = None


def get_frame_processor() -> Any:
	global FRAME_PROCESSOR

	with THREAD_LOCK:
		if FRAME_PROCESSOR is None:
			model_path = get_options('model').get('path')
			FRAME_PROCESSOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_providers))
	return FRAME_PROCESSOR


def clear_frame_processor() -> None:
	global FRAME_PROCESSOR

	FRAME_PROCESSOR = None


def get_options(key : Literal['model']) -> Any:
	global OPTIONS

	if OPTIONS is None:
		OPTIONS =\
		{
			'model': MODELS[frame_processors_globals.frame_enhancer_model]
		}
	return OPTIONS.get(key)


def set_options(key : Literal['model'], value : Any) -> None:
	global OPTIONS

	OPTIONS[key] = value


def register_args(program : ArgumentParser) -> None:
	program.add_argument('--frame-enhancer-model', help = wording.get('help.frame_enhancer_model'), default = config.get_str_value('frame_processors.frame_enhancer_model', 'parimg_compact_x2'), choices = frame_processors_choices.frame_enhancer_models)
	program.add_argument('--frame-enhancer-blend', help = wording.get('help.frame_enhancer_blend'), type = int, default = config.get_int_value('frame_processors.frame_enhancer_blend', '80'), choices = frame_processors_choices.frame_enhancer_blend_range, metavar = create_metavar(frame_processors_choices.frame_enhancer_blend_range))


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.frame_enhancer_model = args.frame_enhancer_model
	frame_processors_globals.frame_enhancer_blend = args.frame_enhancer_blend


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_url = get_options('model').get('url')
		conditional_download(download_directory_path, [ model_url ])
	return True


def post_check() -> bool:
	model_url = get_options('model').get('url')
	model_path = get_options('model').get('path')
	if not facefusion.globals.skip_download and not is_download_done(model_url, model_path):
		logger.error(wording.get('model_download_not_done') + wording.get('exclamation_mark'), NAME)
		return False
	elif not is_file(model_path):
		logger.error(wording.get('model_file_not_present') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode == 'output' and not facefusion.globals.output_path:
		logger.error(wording.get('select_file_or_directory_output') + wording.get('exclamation_mark'), NAME)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	if facefusion.globals.video_memory_strategy == 'strict' or facefusion.globals.video_memory_strategy == 'moderate':
		clear_frame_processor()
	if facefusion.globals.video_memory_strategy == 'strict':
		clear_face_analyser()
		clear_content_analyser()


def enhance_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	size = get_options('model').get('size')
	temp_height, temp_width = temp_vision_frame.shape[:2]
	tile_vision_frames, pad_width, pad_height = create_tile_frames(temp_vision_frame, size)

	for index, tile_vision_frame in enumerate(tile_vision_frames):
		tile_vision_frame = frame_processor.run(None,
		{
			frame_processor.get_inputs()[0].name : prepare_tile_frame(tile_vision_frame)
		})[0]
		tile_vision_frames[index] = normalize_tile_frame(tile_vision_frame, size)
	merge_vision_frame = merge_tile_frames(tile_vision_frames, temp_width, temp_height, pad_width, pad_height, size)
	temp_vision_frame = blend_frame(temp_vision_frame, merge_vision_frame)
	return temp_vision_frame


def prepare_tile_frame(vision_tile_frame : VisionFrame) -> VisionFrame:
	vision_tile_frame = numpy.expand_dims(vision_tile_frame[:,:,::-1], axis = 0)
	vision_tile_frame = vision_tile_frame.transpose(0, 3, 1, 2)
	vision_tile_frame = vision_tile_frame.astype(numpy.float32) / 255
	return vision_tile_frame


def normalize_tile_frame(vision_tile_frame : VisionFrame, size : Size) -> VisionFrame:
	vision_tile_frame = vision_tile_frame.transpose(0, 2, 3, 1).squeeze(0) * 255
	vision_tile_frame = vision_tile_frame.clip(0, 255).astype(numpy.uint8)[:,:,::-1]
	vision_tile_frame = cv2.resize(vision_tile_frame, (size[0], size[0]))
	return vision_tile_frame


def blend_frame(temp_vision_frame : VisionFrame, paste_vision_frame : VisionFrame) -> VisionFrame:
	frame_enhancer_blend = 1 - (frame_processors_globals.frame_enhancer_blend / 100)
	temp_vision_frame = cv2.resize(temp_vision_frame, (paste_vision_frame.shape[1], paste_vision_frame.shape[0]))
	temp_vision_frame = cv2.addWeighted(temp_vision_frame, frame_enhancer_blend, paste_vision_frame, 1 - frame_enhancer_blend, 0)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FrameEnhancerInputs) -> VisionFrame:
	target_vision_frame = inputs['target_vision_frame']
	return enhance_frame(target_vision_frame)


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProcess) -> None:
	for queue_payload in process_manager.manage(queue_payloads):
		target_vision_path = queue_payload['frame_path']
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress()


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	frame_processors.multi_process_frames(None, temp_frame_paths, process_frames)
