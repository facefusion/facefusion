from argparse import ArgumentParser
from functools import lru_cache, partial
from typing import List, Tuple

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, inference_manager, logger, state_manager, translator, video_manager
from facefusion.common_helper import is_macos
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.filesystem import in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.normalizer import normalize_color
from facefusion.processors.modules.background_remover import choices as background_remover_choices
from facefusion.processors.modules.background_remover.types import BackgroundRemoverInputs
from facefusion.processors.types import ProcessorOutputs
from facefusion.program_helper import find_argument_group
from facefusion.sanitizer import sanitize_int_range
from facefusion.thread_helper import thread_semaphore
from facefusion.types import ApplyStateItem, Args, DownloadScope, ExecutionProvider, InferencePool, Mask, ModelOptions, ModelSet, ProcessMode, VisionFrame
from facefusion.vision import read_static_image, read_static_video_frame


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'ben_2':
		{
			'__metadata__':
			{
				'vendor': 'PramaLLC',
				'license': 'MIT',
				'year': 2025
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'ben_2.hash'),
					'path': resolve_relative_path('../.assets/models/ben_2.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'ben_2.onnx'),
					'path': resolve_relative_path('../.assets/models/ben_2.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'birefnet_general':
		{
			'__metadata__':
			{
				'vendor': 'ZhengPeng7',
				'license': 'MIT',
				'year': 2024
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'birefnet_general.hash'),
					'path': resolve_relative_path('../.assets/models/birefnet_general.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'birefnet_general.onnx'),
					'path': resolve_relative_path('../.assets/models/birefnet_general.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'birefnet_portrait':
		{
			'__metadata__':
			{
				'vendor': 'ZhengPeng7',
				'license': 'MIT',
				'year': 2024
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'birefnet_portrait.hash'),
					'path': resolve_relative_path('../.assets/models/birefnet_portrait.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'birefnet_portrait.onnx'),
					'path': resolve_relative_path('../.assets/models/birefnet_portrait.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'isnet_general':
		{
			'__metadata__':
			{
				'vendor': 'xuebinqin',
				'license': 'Apache-2.0',
				'year': 2022
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'isnet_general.hash'),
					'path': resolve_relative_path('../.assets/models/isnet_general.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'isnet_general.onnx'),
					'path': resolve_relative_path('../.assets/models/isnet_general.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'modnet':
		{
			'__metadata__':
			{
				'vendor': 'ZHKKKe',
				'license': 'Apache-2.0',
				'year': 2020
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'modnet.hash'),
					'path': resolve_relative_path('../.assets/models/modnet.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'modnet.onnx'),
					'path': resolve_relative_path('../.assets/models/modnet.onnx')
				}
			},
			'size': (512, 512),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'ormbg':
		{
			'__metadata__':
			{
				'vendor': 'schirrmacher',
				'license': 'Apache-2.0',
				'year': 2024
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'ormbg.hash'),
					'path': resolve_relative_path('../.assets/models/ormbg.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'ormbg.onnx'),
					'path': resolve_relative_path('../.assets/models/ormbg.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'rmbg_1.4':
		{
			'__metadata__':
			{
				'vendor': 'Bria',
				'license': 'Non-Commercial',
				'year': 2023
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'rmbg_1.4.hash'),
					'path': resolve_relative_path('../.assets/models/rmbg_1.4.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'rmbg_1.4.onnx'),
					'path': resolve_relative_path('../.assets/models/rmbg_1.4.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'rmbg_2.0':
		{
			'__metadata__':
			{
				'vendor': 'Bria',
				'license': 'Non-Commercial',
				'year': 2024
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'rmbg_2.0.hash'),
					'path': resolve_relative_path('../.assets/models/rmbg_2.0.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'rmbg_2.0.onnx'),
					'path': resolve_relative_path('../.assets/models/rmbg_2.0.onnx')
				}
			},
			'size': (1024, 1024),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'silueta':
		{
			'__metadata__':
			{
				'vendor': 'Kikedao',
				'license': 'Apache-2.0',
				'year': 2022
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'silueta.hash'),
					'path': resolve_relative_path('../.assets/models/silueta.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'silueta.onnx'),
					'path': resolve_relative_path('../.assets/models/silueta.onnx')
				}
			},
			'size': (320, 320),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'u2net_cloth':
		{
			'__metadata__':
			{
				'vendor': 'levindabhi',
				'license': 'MIT',
				'year': 2021
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_cloth.hash'),
					'path': resolve_relative_path('../.assets/models/u2net_cloth.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_cloth.onnx'),
					'path': resolve_relative_path('../.assets/models/u2net_cloth.onnx')
				}
			},
			'size': (768, 768),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'u2net_general':
		{
			'__metadata__':
			{
				'vendor': 'xuebinqin',
				'license': 'Apache-2.0',
				'year': 2020
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_general.hash'),
					'path': resolve_relative_path('../.assets/models/u2net_general.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_general.onnx'),
					'path': resolve_relative_path('../.assets/models/u2net_general.onnx')
				}
			},
			'size': (320, 320),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'u2net_human':
		{
			'__metadata__':
			{
				'vendor': 'xuebinqin',
				'license': 'Apache-2.0',
				'year': 2021
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_human.hash'),
					'path': resolve_relative_path('../.assets/models/u2net_human.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2net_human.onnx'),
					'path': resolve_relative_path('../.assets/models/u2net_human.onnx')
				}
			},
			'size': (320, 320),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'u2netp':
		{
			'__metadata__':
			{
				'vendor': 'xuebinqin',
				'license': 'Apache-2.0',
				'year': 2021
			},
			'hashes':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2netp.hash'),
					'path': resolve_relative_path('../.assets/models/u2netp.hash')
				}
			},
			'sources':
			{
				'background_remover':
				{
					'url': resolve_download_url('models-3.5.0', 'u2netp.onnx'),
					'path': resolve_relative_path('../.assets/models/u2netp.onnx')
				}
			},
			'size': (320, 320),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('background_remover_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('background_remover_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def resolve_execution_providers() -> List[ExecutionProvider]:
	if is_macos() and has_execution_provider('coreml'):
		return [ 'cpu' ]
	return state_manager.get_item('execution_providers')


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('background_remover_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--background-remover-model', help = translator.get('help.model', __package__), default = config.get_str_value('processors', 'background_remover_model', 'rmbg_2.0'), choices = background_remover_choices.background_remover_models)
		group_processors.add_argument('--background-remover-color', help = translator.get('help.color', __package__), type = partial(sanitize_int_range, int_range = background_remover_choices.background_remover_color_range), default = config.get_int_list('processors', 'background_remover_color', '0 0 0 0'), nargs ='+')
		facefusion.jobs.job_store.register_step_keys([ 'background_remover_model', 'background_remover_color' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('background_remover_model', args.get('background_remover_model'))
	apply_state_item('background_remover_color', normalize_color(args.get('background_remover_color')))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(translator.get('choose_image_or_video_target') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(translator.get('specify_image_or_video_output') + translator.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(translator.get('match_target_and_output_extension') + translator.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_video_frame.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()


def remove_background(temp_vision_frame : VisionFrame) -> Tuple[VisionFrame, Mask]:
	temp_vision_mask = forward(prepare_temp_frame(temp_vision_frame))
	temp_vision_mask = normalize_vision_mask(temp_vision_mask)
	temp_vision_mask = cv2.resize(temp_vision_mask, temp_vision_frame.shape[:2][::-1])
	temp_vision_frame = apply_background_color(temp_vision_frame, temp_vision_mask)
	return temp_vision_frame, temp_vision_mask


def forward(temp_vision_frame : VisionFrame) -> VisionFrame:
	background_remover = get_inference_pool().get('background_remover')
	model_name = state_manager.get_item('background_remover_model')

	with thread_semaphore():
		remove_vision_frame = background_remover.run(None,
		{
			'input': temp_vision_frame
		})[0]

		if model_name == 'u2net_cloth':
			remove_vision_frame = numpy.argmax(remove_vision_frame, axis = 1)

	return remove_vision_frame


def prepare_temp_frame(temp_vision_frame : VisionFrame) -> VisionFrame:
	model_size = get_model_options().get('size')
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')

	temp_vision_frame = cv2.resize(temp_vision_frame, model_size)
	temp_vision_frame = temp_vision_frame[:, :, ::-1] / 255.0
	temp_vision_frame = (temp_vision_frame - model_mean) / model_standard_deviation
	temp_vision_frame = temp_vision_frame.transpose(2, 0, 1)
	temp_vision_frame = numpy.expand_dims(temp_vision_frame, axis = 0).astype(numpy.float32)
	return temp_vision_frame


def normalize_vision_mask(temp_vision_mask : Mask) -> Mask:
	temp_vision_mask = numpy.squeeze(temp_vision_mask).clip(0, 1) * 255
	temp_vision_mask = numpy.clip(temp_vision_mask, 0, 255).astype(numpy.uint8)
	return temp_vision_mask


def apply_background_color(temp_vision_frame : VisionFrame, temp_vision_mask : Mask) -> VisionFrame:
	background_remover_color = state_manager.get_item('background_remover_color')
	temp_vision_mask = temp_vision_mask.astype(numpy.float32) / 255
	temp_vision_mask = numpy.expand_dims(temp_vision_mask, axis = 2)
	temp_vision_mask = (1 - temp_vision_mask) * background_remover_color[-1] / 255
	color_frame = numpy.zeros_like(temp_vision_frame)
	color_frame[:, :, 0] = background_remover_color[2]
	color_frame[:, :, 1] = background_remover_color[1]
	color_frame[:, :, 2] = background_remover_color[0]
	temp_vision_frame = temp_vision_frame * (1 - temp_vision_mask) + color_frame * temp_vision_mask
	temp_vision_frame = temp_vision_frame.astype(numpy.uint8)
	return temp_vision_frame


def process_frame(inputs : BackgroundRemoverInputs) -> ProcessorOutputs:
	temp_vision_frame = inputs.get('temp_vision_frame')
	temp_vision_frame, temp_vision_mask = remove_background(temp_vision_frame)
	temp_vision_mask = numpy.minimum.reduce([ temp_vision_mask, inputs.get('temp_vision_mask') ])
	return temp_vision_frame, temp_vision_mask
