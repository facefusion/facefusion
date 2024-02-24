from typing import Any, List, Literal, Optional, Tuple
from argparse import ArgumentParser
import threading
import cv2
import numpy
import onnxruntime
import facefusion.globals
import facefusion.processors.frame.core as frame_processors
from facefusion import config, logger, wording
from facefusion.face_analyser import clear_face_analyser
from facefusion.content_analyser import clear_content_analyser
from facefusion.execution_helper import apply_execution_provider_options
from facefusion.typing import Face, VisionFrame, Update_Process, ProcessMode, ModelSet, OptionsWithModel, QueuePayload
from facefusion.common_helper import create_metavar
from facefusion.filesystem import is_file, resolve_relative_path
from facefusion.download import conditional_download, is_download_done
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.processors.frame.typings import FrameEnhancerInputs
from facefusion.processors.frame import globals as frame_processors_globals
from facefusion.processors.frame import choices as frame_processors_choices

FRAME_PROCESSOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
NAME = __name__.upper()
MODELS : ModelSet =\
{
	'real_esrgan_x4':
	{
		'url': 'https://filebin.net/f5fg25rlfci17kjo/realesrganx4.onnx',
		'path': resolve_relative_path('../.assets/models/realesrganx4.onnx'),
		'scale': 4,
		'tile_size': 128,
	},
	'hfa2k_x4':
	{
		'url': 'https://github.com/Phhofm/models/raw/main/4xHFA2k/4xHFA2k_fp32.onnx',
		'path': resolve_relative_path('../.assets/models/4xHFA2k/4xHFA2k_fp32.onnx'),
		'scale': 4,
		'tile_size': 256,
	},
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
	program.add_argument('--frame-enhancer-model', help = wording.get('help.frame_enhancer_model'), default = config.get_str_value('frame_processors.frame_enhancer_model', 'real_esrgan_x4'), choices = frame_processors_choices.frame_enhancer_models)
	program.add_argument('--frame-enhancer-blend', help = wording.get('help.frame_enhancer_blend'), type = int, default = config.get_int_value('frame_processors.frame_enhancer_blend', '80'), choices = frame_processors_choices.frame_enhancer_blend_range, metavar = create_metavar(frame_processors_choices.frame_enhancer_blend_range))
	program.add_argument('--frame-enhancer-disable-upscale', help = wording.get('help.frame_enhancer_disable_upscale'), action = 'store_true', default = False)


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	frame_processors_globals.frame_enhancer_model = args.frame_enhancer_model
	frame_processors_globals.frame_enhancer_blend = args.frame_enhancer_blend
	frame_processors_globals.frame_enhancer_disable_upscale = args.frame_enhancer_disable_upscale


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


def split_frame_into_tiles(frame: VisionFrame, tile_size : int, pad_size : int) -> Tuple[numpy.ndarray[Any, Any], Tuple[int, int, int]]:
    pad_size_bottom = pad_size + tile_size - frame.shape[0] % tile_size
    pad_size_right = pad_size + tile_size - frame.shape[1] % tile_size
    pad_frame = cv2.copyMakeBorder(frame, pad_size, pad_size_bottom, pad_size, pad_size_right, cv2.BORDER_REPLICATE)
    tiles = []
    for row in range(pad_size, pad_frame.shape[0] - pad_size, tile_size):
        for column in range(pad_size, pad_frame.shape[1] - pad_size, tile_size):
            top = row - pad_size
            bottom = row + pad_size + tile_size
            left = column - pad_size
            right = column + pad_size + tile_size
            tiles.append(pad_frame[top : bottom, left : right, :])
    return numpy.array(tiles), pad_frame.shape


def stitch_tiles_into_frame(tiles : numpy.ndarray[Any, Any], pad_frame_shape : Tuple[int, int, int], target_shape : Tuple[int, int, int], pad_size: int) -> VisionFrame:
    tiles = tiles[:, pad_size:-pad_size, pad_size:-pad_size, :]
    tile_height, tile_width, _ = tiles.shape[1:]
    tiles_per_row = min(pad_frame_shape[1] // tile_width, len(tiles))
    frame = numpy.zeros(pad_frame_shape)
    for index, tile in enumerate(tiles):
        top = (index // tiles_per_row) * tile_height
        bottom = top + tile_height
        left = (index % tiles_per_row) * tile_width
        right = left + tile_width
        frame[top : bottom, left : right, :] = tile
    frame = frame[:target_shape[0], :target_shape[1], :].astype(numpy.uint8)
    return frame


def enhance_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	frame_processor = get_frame_processor()
	pre_pad_size = 15
	pad_size = 24
	scale = get_options('model').get('scale')
	tile_size = get_options('model').get('tile_size') - (2 * pad_size)
	temp_vision_frame = cv2.copyMakeBorder(temp_vision_frame, pre_pad_size, pre_pad_size, pre_pad_size, pre_pad_size, cv2.BORDER_REFLECT)
	tiles, pad_frame_shape = split_frame_into_tiles(temp_vision_frame, tile_size, pad_size)
	tiles = tiles.transpose(0, 3, 1, 2).astype(numpy.float32) / 255
	with THREAD_SEMAPHORE:
		enhanced_tiles = frame_processor.run(None, {frame_processor.get_inputs()[0].name : [tiles[0]]})[0]
		for index in range(1, tiles.shape[0]):
			enhanced_tiles = numpy.concatenate((enhanced_tiles, frame_processor.run(None, {frame_processor.get_inputs()[0].name : [tiles[index]]})[0]), 0)
	enhanced_tiles = (enhanced_tiles.transpose(0, 2, 3, 1) * 255).clip(0, 255).astype(numpy.uint8)
	if frame_processors_globals.frame_enhancer_disable_upscale:
		enhanced_tiles = numpy.array([cv2.resize(enhanced_tile, tiles.shape[2:4]) for enhanced_tile in enhanced_tiles])
		temp_vision_frame_shape = (temp_vision_frame.shape[0], temp_vision_frame.shape[1], 3)
	else:
		pad_frame_shape = tuple(numpy.multiply(pad_frame_shape[0:2], scale)) + (3,)
		temp_vision_frame_shape = tuple(numpy.multiply(temp_vision_frame.shape[0:2], scale)) + (3,)
		pre_pad_size *= scale
		pad_size *= scale
	paste_vision_frame = stitch_tiles_into_frame(enhanced_tiles, pad_frame_shape, temp_vision_frame_shape, pad_size)
	temp_vision_frame = blend_frame(temp_vision_frame, paste_vision_frame)
	temp_vision_frame = temp_vision_frame[pre_pad_size:-pre_pad_size, pre_pad_size:-pre_pad_size, :]
	return temp_vision_frame


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


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : Update_Process) -> None:
	for queue_payload in queue_payloads:
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
