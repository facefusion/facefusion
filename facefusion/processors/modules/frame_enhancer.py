from argparse import ArgumentParser
from functools import lru_cache
from typing import List

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
import facefusion.processors.core as processors
from facefusion import config, content_analyser, inference_manager, logger, process_manager, state_manager, video_manager, wording
from facefusion.common_helper import create_int_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FrameEnhancerInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, QueuePayload, UpdateProgress, VisionFrame
from facefusion.vision import create_tile_frames, merge_tile_frames, read_image, read_static_image, write_image


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'clear_reality_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'clear_reality_x4.hash'),
					'path': resolve_relative_path('../.assets/models/clear_reality_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'clear_reality_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/clear_reality_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'lsdir_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'lsdir_x4.hash'),
					'path': resolve_relative_path('../.assets/models/lsdir_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'lsdir_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/lsdir_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'nomos8k_sc_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'nomos8k_sc_x4.hash'),
					'path': resolve_relative_path('../.assets/models/nomos8k_sc_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'nomos8k_sc_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/nomos8k_sc_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'real_esrgan_x2':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x2.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x2.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x2.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x2.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 2
		},
		'real_esrgan_x2_fp16':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x2_fp16.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x2_fp16.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x2_fp16.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x2_fp16.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 2
		},
		'real_esrgan_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x4.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x4.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 4
		},
		'real_esrgan_x4_fp16':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x4_fp16.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x4_fp16.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x4_fp16.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x4_fp16.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 4
		},
		'real_esrgan_x8':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x8.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x8.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x8.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x8.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 8
		},
		'real_esrgan_x8_fp16':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x8_fp16.hash'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x8_fp16.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_esrgan_x8_fp16.onnx'),
					'path': resolve_relative_path('../.assets/models/real_esrgan_x8_fp16.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 8
		},
		'real_hatgan_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_hatgan_x4.hash'),
					'path': resolve_relative_path('../.assets/models/real_hatgan_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'real_hatgan_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/real_hatgan_x4.onnx')
				}
			},
			'size': (256, 16, 8),
			'scale': 4
		},
		'real_web_photo_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'real_web_photo_x4.hash'),
					'path': resolve_relative_path('../.assets/models/real_web_photo_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'real_web_photo_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/real_web_photo_x4.onnx')
				}
			},
			'size': (64, 4, 2),
			'scale': 4
		},
		'realistic_rescaler_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'realistic_rescaler_x4.hash'),
					'path': resolve_relative_path('../.assets/models/realistic_rescaler_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'realistic_rescaler_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/realistic_rescaler_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'remacri_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'remacri_x4.hash'),
					'path': resolve_relative_path('../.assets/models/remacri_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'remacri_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/remacri_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'siax_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'siax_x4.hash'),
					'path': resolve_relative_path('../.assets/models/siax_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'siax_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/siax_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'span_kendata_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'span_kendata_x4.hash'),
					'path': resolve_relative_path('../.assets/models/span_kendata_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'span_kendata_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/span_kendata_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'swin2_sr_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'swin2_sr_x4.hash'),
					'path': resolve_relative_path('../.assets/models/swin2_sr_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.1.0', 'swin2_sr_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/swin2_sr_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'ultra_sharp_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'ultra_sharp_x4.hash'),
					'path': resolve_relative_path('../.assets/models/ultra_sharp_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.0.0', 'ultra_sharp_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/ultra_sharp_x4.onnx')
				}
			},
			'size': (128, 8, 4),
			'scale': 4
		},
		'ultra_sharp_2_x4':
		{
			'hashes':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.3.0', 'ultra_sharp_2_x4.hash'),
					'path': resolve_relative_path('../.assets/models/ultra_sharp_2_x4.hash')
				}
			},
			'sources':
			{
				'frame_enhancer':
				{
					'url': resolve_download_url('models-3.3.0', 'ultra_sharp_2_x4.onnx'),
					'path': resolve_relative_path('../.assets/models/ultra_sharp_2_x4.onnx')
				}
			},
			'size': (1024, 64, 32),
			'scale': 4
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ get_frame_enhancer_model() ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ get_frame_enhancer_model() ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = get_frame_enhancer_model()
	return create_static_model_set('full').get(model_name)


def get_frame_enhancer_model() -> str:
	frame_enhancer_model = state_manager.get_item('frame_enhancer_model')

	if has_execution_provider('coreml'):
		if frame_enhancer_model == 'real_esrgan_x2_fp16':
			return 'real_esrgan_x2'
		if frame_enhancer_model == 'real_esrgan_x4_fp16':
			return 'real_esrgan_x4'
		if frame_enhancer_model == 'real_esrgan_x8_fp16':
			return 'real_esrgan_x8'
	return frame_enhancer_model


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--frame-enhancer-model', help = wording.get('help.frame_enhancer_model'), default = config.get_str_value('processors', 'frame_enhancer_model', 'span_kendata_x4'), choices = processors_choices.frame_enhancer_models)
		group_processors.add_argument('--frame-enhancer-blend', help = wording.get('help.frame_enhancer_blend'), type = int, default = config.get_int_value('processors', 'frame_enhancer_blend', '80'), choices = processors_choices.frame_enhancer_blend_range, metavar = create_int_metavar(processors_choices.frame_enhancer_blend_range))
		facefusion.jobs.job_store.register_step_keys([ 'frame_enhancer_model', 'frame_enhancer_blend' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('frame_enhancer_model', args.get('frame_enhancer_model'))
	apply_state_item('frame_enhancer_blend', args.get('frame_enhancer_blend'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(wording.get('choose_image_or_video_target') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(wording.get('specify_image_or_video_output') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(wording.get('match_target_and_output_extension') + wording.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()


def enhance_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	model_size = get_model_options().get('size')
	model_scale = get_model_options().get('scale')
	temp_height, temp_width = temp_vision_frame.shape[:2]
	tile_vision_frames, pad_width, pad_height = create_tile_frames(temp_vision_frame, model_size)

	for index, tile_vision_frame in enumerate(tile_vision_frames):
		tile_vision_frame = prepare_tile_frame(tile_vision_frame)
		tile_vision_frame = forward(tile_vision_frame)
		tile_vision_frames[index] = normalize_tile_frame(tile_vision_frame)

	merge_vision_frame = merge_tile_frames(tile_vision_frames, temp_width * model_scale, temp_height * model_scale, pad_width * model_scale, pad_height * model_scale, (model_size[0] * model_scale, model_size[1] * model_scale, model_size[2] * model_scale))
	temp_vision_frame = blend_frame(temp_vision_frame, merge_vision_frame)
	return temp_vision_frame


def forward(tile_vision_frame : VisionFrame) -> VisionFrame:
	frame_enhancer = get_inference_pool().get('frame_enhancer')

	with conditional_thread_semaphore():
		tile_vision_frame = frame_enhancer.run(None,
		{
			'input': tile_vision_frame
		})[0]

	return tile_vision_frame


def prepare_tile_frame(vision_tile_frame : VisionFrame) -> VisionFrame:
	vision_tile_frame = numpy.expand_dims(vision_tile_frame[:, :, ::-1], axis = 0)
	vision_tile_frame = vision_tile_frame.transpose(0, 3, 1, 2)
	vision_tile_frame = vision_tile_frame.astype(numpy.float32) / 255.0
	return vision_tile_frame


def normalize_tile_frame(vision_tile_frame : VisionFrame) -> VisionFrame:
	vision_tile_frame = vision_tile_frame.transpose(0, 2, 3, 1).squeeze(0) * 255
	vision_tile_frame = vision_tile_frame.clip(0, 255).astype(numpy.uint8)[:, :, ::-1]
	return vision_tile_frame


def blend_frame(temp_vision_frame : VisionFrame, merge_vision_frame : VisionFrame) -> VisionFrame:
	frame_enhancer_blend = 1 - (state_manager.get_item('frame_enhancer_blend') / 100)
	temp_vision_frame = cv2.resize(temp_vision_frame, (merge_vision_frame.shape[1], merge_vision_frame.shape[0]))
	temp_vision_frame = cv2.addWeighted(temp_vision_frame, frame_enhancer_blend, merge_vision_frame, 1 - frame_enhancer_blend, 0)
	return temp_vision_frame


def get_reference_frame(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	pass


def process_frame(inputs : FrameEnhancerInputs) -> VisionFrame:
	target_vision_frame = inputs.get('target_vision_frame')
	return enhance_frame(target_vision_frame)


def process_frames(source_paths : List[str], queue_payloads : List[QueuePayload], update_progress : UpdateProgress) -> None:
	for queue_payload in process_manager.manage(queue_payloads):
		target_vision_path = queue_payload['frame_path']
		target_vision_frame = read_image(target_vision_path)
		output_vision_frame = process_frame(
		{
			'target_vision_frame': target_vision_frame
		})
		write_image(target_vision_path, output_vision_frame)
		update_progress(1)


def process_image(source_paths : List[str], target_path : str, output_path : str) -> None:
	target_vision_frame = read_static_image(target_path)
	output_vision_frame = process_frame(
	{
		'target_vision_frame': target_vision_frame
	})
	write_image(output_path, output_vision_frame)


def process_video(source_paths : List[str], temp_frame_paths : List[str]) -> None:
	processors.multi_process_frames(None, temp_frame_paths, process_frames)
