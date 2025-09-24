from argparse import ArgumentParser
from functools import lru_cache
from typing import List, Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from time import time
from facefusion import profiler

import cv2
import numpy

import facefusion.choices
import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, face_tracker, inference_manager, logger, state_manager, tensorrt_runner, video_manager, wording
from facefusion.common_helper import get_first, is_macos
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.execution import has_execution_provider
from facefusion.face_analyser import get_average_face, get_many_faces, get_one_face, scale_face
from facefusion.face_helper import paste_back, warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.face_selector import select_faces, sort_faces_by_order
from facefusion.filesystem import filter_image_paths, has_image, in_directory, is_image, is_video, resolve_relative_path, same_file_extension
from facefusion.model_helper import get_static_model_initializer
from facefusion.processors import choices as processors_choices
from facefusion.processors.pixel_boost import explode_pixel_boost, implode_pixel_boost
from facefusion.processors.types import FaceSwapperInputs
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.hash_helper import create_hash
from facefusion.types import ApplyStateItem, Args, DownloadScope, Embedding, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, VisionFrame
from facefusion.vision import read_static_image, read_static_images, read_static_video_frame, unpack_resolution

# Shared caches for multi-threaded frame processing
CACHE_LOCK = thread_lock()
_SOURCE_FACE_CACHE : Dict[str, Face] = {}
_SOURCE_EMBEDDING_CACHE : Dict[str, Embedding] = {}

# Optional CUDA I/O binding via CuPy (reduces copies on CUDA EP)
try:
    import cupy as cp  # type: ignore
    _HAS_CUPY = True
except Exception:
    _HAS_CUPY = False

_GPU_MODEL_STATS: Dict[Tuple[float, ...], Any] = {}

# Dynamic strategy heuristic for CPU/CoreML
_HEURISTIC_FRAMES_TO_OBSERVE = 12
_heuristic_state : Dict[str, Any] = {
    'observed': 0,
    'single_or_zero_frames': 0,
    'decided': False,
    'prefer_sequential': False
}

def _is_gpu_providers() -> bool:
    providers = [str(p).lower() for p in (state_manager.get_item('execution_providers') or [])]
    return any(p in ('cuda', 'tensorrt') for p in providers)

def _record_face_count_for_heuristic(face_count: int) -> None:
    if _is_gpu_providers():
        # Always batch on GPU; no heuristic needed
        _heuristic_state['decided'] = True
        _heuristic_state['prefer_sequential'] = False
        return
    if _heuristic_state['decided']:
        return
    _heuristic_state['observed'] += 1
    if face_count <= 1:
        _heuristic_state['single_or_zero_frames'] += 1
    if _heuristic_state['observed'] >= _HEURISTIC_FRAMES_TO_OBSERVE:
        ratio = _heuristic_state['single_or_zero_frames'] / max(1, _heuristic_state['observed'])
        _heuristic_state['prefer_sequential'] = ratio >= 0.8
        _heuristic_state['decided'] = True


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'blendswap_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'blendswap_256.hash'),
					'path': resolve_relative_path('../.assets/models/blendswap_256.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'blendswap_256.onnx'),
					'path': resolve_relative_path('../.assets/models/blendswap_256.onnx')
				}
			},
			'type': 'blendswap',
			'template': 'ffhq_512',
			'size': (256, 256),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'ghost_1_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_1_256.hash'),
					'path': resolve_relative_path('../.assets/models/ghost_1_256.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_1_256.onnx'),
					'path': resolve_relative_path('../.assets/models/ghost_1_256.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.onnx')
				}
			},
			'type': 'ghost',
			'template': 'arcface_112_v1',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'ghost_2_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_2_256.hash'),
					'path': resolve_relative_path('../.assets/models/ghost_2_256.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_2_256.onnx'),
					'path': resolve_relative_path('../.assets/models/ghost_2_256.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.onnx')
				}
			},
			'type': 'ghost',
			'template': 'arcface_112_v1',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'ghost_3_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_3_256.hash'),
					'path': resolve_relative_path('../.assets/models/ghost_3_256.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'ghost_3_256.onnx'),
					'path': resolve_relative_path('../.assets/models/ghost_3_256.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_ghost.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_ghost.onnx')
				}
			},
			'type': 'ghost',
			'template': 'arcface_112_v1',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'hififace_unofficial_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.1.0', 'hififace_unofficial_256.hash'),
					'path': resolve_relative_path('../.assets/models/hififace_unofficial_256.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_hififace.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_hififace.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.1.0', 'hififace_unofficial_256.onnx'),
					'path': resolve_relative_path('../.assets/models/hififace_unofficial_256.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_hififace.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_hififace.onnx')
				}
			},
			'type': 'hififace',
			'template': 'mtcnn_512',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'hyperswap_1a_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.3.0', 'hyperswap_1a_256.hash'),
					'path': resolve_relative_path('../.assets/models/hyperswap_1a_256.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.3.0', 'hyperswap_1a_256.onnx'),
					'path': resolve_relative_path('../.assets/models/hyperswap_1a_256.onnx')
				}
			},
			'type': 'hyperswap',
			'template': 'arcface_128',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'hyperswap_1b_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.3.0', 'hyperswap_1b_256.hash'),
					'path': resolve_relative_path('../.assets/models/hyperswap_1b_256.hash')
				}
			},
			'sources':
				{
					'face_swapper':
					{
						'url': resolve_download_url('models-3.3.0', 'hyperswap_1b_256.onnx'),
						'path': resolve_relative_path('../.assets/models/hyperswap_1b_256.onnx')
					}
				},
			'type': 'hyperswap',
			'template': 'arcface_128',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'hyperswap_1c_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.3.0', 'hyperswap_1c_256.hash'),
					'path': resolve_relative_path('../.assets/models/hyperswap_1c_256.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.3.0', 'hyperswap_1c_256.onnx'),
					'path': resolve_relative_path('../.assets/models/hyperswap_1c_256.onnx')
				}
			},
			'type': 'hyperswap',
			'template': 'arcface_128',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		},
		'inswapper_128':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'inswapper_128.hash'),
					'path': resolve_relative_path('../.assets/models/inswapper_128.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'inswapper_128.onnx'),
					'path': resolve_relative_path('../.assets/models/inswapper_128.onnx')
				}
			},
			'type': 'inswapper',
			'template': 'arcface_128',
			'size': (128, 128),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'inswapper_128_fp16':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'inswapper_128_fp16.hash'),
					'path': resolve_relative_path('../.assets/models/inswapper_128_fp16.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'inswapper_128_fp16.onnx'),
					'path': resolve_relative_path('../.assets/models/inswapper_128_fp16.onnx')
				}
			},
			'type': 'inswapper',
			'template': 'arcface_128',
			'size': (128, 128),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'simswap_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'simswap_256.hash'),
					'path': resolve_relative_path('../.assets/models/simswap_256.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_simswap.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_simswap.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'simswap_256.onnx'),
					'path': resolve_relative_path('../.assets/models/simswap_256.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_simswap.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_simswap.onnx')
				}
			},
			'type': 'simswap',
			'template': 'arcface_112_v1',
			'size': (256, 256),
			'mean': [ 0.485, 0.456, 0.406 ],
			'standard_deviation': [ 0.229, 0.224, 0.225 ]
		},
		'simswap_unofficial_512':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'simswap_unofficial_512.hash'),
					'path': resolve_relative_path('../.assets/models/simswap_unofficial_512.hash')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_simswap.hash'),
					'path': resolve_relative_path('../.assets/models/crossface_simswap.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'simswap_unofficial_512.onnx'),
					'path': resolve_relative_path('../.assets/models/simswap_unofficial_512.onnx')
				},
				'embedding_converter':
				{
					'url': resolve_download_url('models-3.4.0', 'crossface_simswap.onnx'),
					'path': resolve_relative_path('../.assets/models/crossface_simswap.onnx')
				}
			},
			'type': 'simswap',
			'template': 'arcface_112_v1',
			'size': (512, 512),
			'mean': [ 0.0, 0.0, 0.0 ],
			'standard_deviation': [ 1.0, 1.0, 1.0 ]
		},
		'uniface_256':
		{
			'hashes':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'uniface_256.hash'),
					'path': resolve_relative_path('../.assets/models/uniface_256.hash')
				}
			},
			'sources':
			{
				'face_swapper':
				{
					'url': resolve_download_url('models-3.0.0', 'uniface_256.onnx'),
					'path': resolve_relative_path('../.assets/models/uniface_256.onnx')
				}
			},
			'type': 'uniface',
			'template': 'ffhq_512',
			'size': (256, 256),
			'mean': [ 0.5, 0.5, 0.5 ],
			'standard_deviation': [ 0.5, 0.5, 0.5 ]
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ get_model_name() ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ get_model_name() ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = get_model_name()
	return create_static_model_set('full').get(model_name)


def get_model_name() -> str:
	model_name = state_manager.get_item('face_swapper_model')

	if is_macos() and has_execution_provider('coreml') and model_name == 'inswapper_128_fp16':
		return 'inswapper_128'
	return model_name


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-swapper-model', help = wording.get('help.face_swapper_model'), default = config.get_str_value('processors', 'face_swapper_model', 'hyperswap_1a_256'), choices = processors_choices.face_swapper_models)
		known_args, _ = program.parse_known_args()
		face_swapper_pixel_boost_choices = processors_choices.face_swapper_set.get(known_args.face_swapper_model)
		group_processors.add_argument('--face-swapper-pixel-boost', help = wording.get('help.face_swapper_pixel_boost'), default = config.get_str_value('processors', 'face_swapper_pixel_boost', get_first(face_swapper_pixel_boost_choices)), choices = face_swapper_pixel_boost_choices)
		group_processors.add_argument('--face-swapper-weight', help = wording.get('help.face_swapper_weight'), type = float, default = config.get_float_value('processors', 'face_swapper_weight', '0.5'), choices = processors_choices.face_swapper_weight_range)
		# Batching control: auto|always|never
		group_processors.add_argument('--face-swapper-batching', help = 'Batching strategy for face swapper: auto, always or never', default = config.get_str_value('processors', 'face_swapper_batching', 'auto'), choices = [ 'auto', 'always', 'never' ])
		default_trt = config.get_bool_value('processors', 'face_swapper_use_trt', 'true')
		group_processors.add_argument('--face-swapper-use-trt', dest = 'face_swapper_use_trt', help = wording.get('help.face_swapper_use_trt'), action = 'store_true', default = True if default_trt is None else default_trt)
		group_processors.add_argument('--face-swapper-disable-trt', dest = 'face_swapper_use_trt', help = wording.get('help.face_swapper_disable_trt'), action = 'store_false')
		group_processors.add_argument('--face-swapper-trt-max-batch', help = wording.get('help.face_swapper_trt_max_batch'), type = int, default = config.get_int_value('processors', 'face_swapper_trt_max_batch', '64'), choices = processors_choices.face_swapper_trt_max_batch_range)
		facefusion.jobs.job_store.register_step_keys([ 'face_swapper_model', 'face_swapper_pixel_boost', 'face_swapper_weight', 'face_swapper_batching', 'face_swapper_use_trt', 'face_swapper_trt_max_batch' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_swapper_model', args.get('face_swapper_model'))
	apply_state_item('face_swapper_pixel_boost', args.get('face_swapper_pixel_boost'))
	apply_state_item('face_swapper_weight', args.get('face_swapper_weight'))
	apply_state_item('face_swapper_batching', args.get('face_swapper_batching'))
	apply_state_item('face_swapper_use_trt', args.get('face_swapper_use_trt'))
	apply_state_item('face_swapper_trt_max_batch', args.get('face_swapper_trt_max_batch'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if not has_image(state_manager.get_item('source_paths')):
		logger.error(wording.get('choose_image_source') + wording.get('exclamation_mark'), __name__)
		return False

	face_tracker.reset_tracker()

	source_image_paths = filter_image_paths(state_manager.get_item('source_paths'))
	source_frames = read_static_images(source_image_paths)
	source_faces = get_many_faces(source_frames, use_tracking = False)

	if not get_one_face(source_faces):
		logger.error(wording.get('no_source_face_detected') + wording.get('exclamation_mark'), __name__)
		return False

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
	read_static_video_frame.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		get_static_model_initializer.cache_clear()
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()
	# Clear local caches between runs
	with CACHE_LOCK:
		_SOURCE_FACE_CACHE.clear()
		_SOURCE_EMBEDDING_CACHE.clear()
	face_tracker.reset_tracker()

def _build_prepared_source_for_face(source_face: Face, target_face: Face) -> Dict[str, Any]:
	"""Precompute the 'source' tensor once per target face.
	- For frame-based models (blendswap/uniface): returns the prepared source frame (1,C,H,W)
	- For embedding-based models: returns the balanced source embedding (1,D)
	"""
	model_type = model_options.get('type')
	if model_type in [ 'blendswap', 'uniface' ]:
		return { 'kind': 'frame', 'tensor': prepare_source_frame(source_face) }
	# embedding-based path
	src = _get_cached_source_embedding(source_face)
	if src is None:
		src = prepare_source_embedding(source_face)
	src = balance_source_embedding(src, target_face.embedding)
	return { 'kind': 'embedding', 'tensor': src }

def _forward_swap_face_prepared(prepared_source: Dict[str, Any], crop_vision_frame: VisionFrame) -> VisionFrame:
	"""Same as forward_swap_face, but uses a precomputed 'source' tensor to avoid per-tile work."""
	face_swapper = get_inference_pool().get('face_swapper')
	model_type = get_model_options().get('type')
	face_swapper_inputs : Dict[str, Any] = {}

	# Keep the CoreML fallback behavior consistent on macOS for certain models
	if is_macos() and has_execution_provider('coreml') and model_type in [ 'ghost', 'uniface' ]:
		face_swapper.set_providers([ facefusion.choices.execution_provider_set.get('cpu') ])

	for face_swapper_input in face_swapper.get_inputs():
		if face_swapper_input.name == 'source':
			face_swapper_inputs[face_swapper_input.name] = prepared_source['tensor']
		elif face_swapper_input.name == 'target':
			face_swapper_inputs[face_swapper_input.name] = crop_vision_frame

	with conditional_thread_semaphore():
		out = face_swapper.run(None, face_swapper_inputs)[0][0]
	return out

def _swap_face_to_layers(prepared_source: Dict[str, Any], target_face: Face, base_frame: VisionFrame) -> Tuple[VisionFrame, numpy.ndarray, numpy.ndarray]:
	"""Heavy compute for one face; return layers to paste.

	Returns: (swapped_crop: HxWx3 uint8-like, crop_mask: HxW float32 in [0,1], affine_matrix)
	"""
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	pixel_boost_size = unpack_resolution(state_manager.get_item('face_swapper_pixel_boost'))
	pixel_boost_total = pixel_boost_size[0] // model_size[0]

	# 1) Warp to face-aligned crop
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(
		base_frame, target_face.landmark_set.get('5/68'), model_template, pixel_boost_size
	)

	# 2) Masks (box/occlusion)
	crop_masks : List[numpy.ndarray] = []
	if 'box' in state_manager.get_item('face_mask_types'):
		box_mask = create_box_mask(crop_vision_frame,
			state_manager.get_item('face_mask_blur'),
			state_manager.get_item('face_mask_padding'))
		crop_masks.append(box_mask)

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	# 3) Pixel-boost tiles -> run model on each tile with precomputed 'source'
	temp_tiles : List[VisionFrame] = []
	pb_tiles = implode_pixel_boost(crop_vision_frame, pixel_boost_total, model_size)
	for tile in pb_tiles:
		tile = prepare_crop_frame(tile)
		tile = _forward_swap_face_prepared(prepared_source, tile)
		tile = normalize_crop_frame(tile)
		temp_tiles.append(tile)
	swapped_crop = explode_pixel_boost(temp_tiles, pixel_boost_total, model_size, pixel_boost_size)

	# 4) Extra masks (area/region) computed on the final crop
	if 'area' in state_manager.get_item('face_mask_types'):
		face_landmark_68 = cv2.transform(target_face.landmark_set.get('68').reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
		area_mask = create_area_mask(swapped_crop, face_landmark_68, state_manager.get_item('face_mask_areas'))
		crop_masks.append(area_mask)

	if 'region' in state_manager.get_item('face_mask_types'):
		region_mask = create_region_mask(swapped_crop, state_manager.get_item('face_mask_regions'))
		crop_masks.append(region_mask)

	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1) if crop_masks else numpy.ones(swapped_crop.shape[:2], dtype=numpy.float32)
	return swapped_crop, crop_mask, affine_matrix

def _build_source_key() -> str:
	"""Create a stable key for current source(s) and model to cache face/embedding."""
	source_paths = state_manager.get_item('source_paths') or []
	model_name = get_model_name()
	parts : List[str] = [model_name]
	for p in source_paths:
		try:
			with open(p, 'rb') as f:
				parts.append(create_hash(f.read()))
		except Exception:
			parts.append(p)
	return '|'.join(parts)

def _get_cached_source_face(source_vision_frames : List[VisionFrame]) -> Optional[Face]:
	key = _build_source_key()
	with CACHE_LOCK:
		cached = _SOURCE_FACE_CACHE.get(key)
	if cached:
		return cached
	# Fallback: extract and cache
	source_face = extract_source_face(source_vision_frames)
	if source_face:
		with CACHE_LOCK:
			_SOURCE_FACE_CACHE[key] = source_face
	return source_face

def _get_cached_source_embedding(source_face : Face) -> Optional[Embedding]:
	key = _build_source_key() + '#embedding'
	with CACHE_LOCK:
		cached = _SOURCE_EMBEDDING_CACHE.get(key)
	if cached is not None:
		return cached
	try:
		emb = prepare_source_embedding(source_face)
		with CACHE_LOCK:
			_SOURCE_EMBEDDING_CACHE[key] = emb
		return emb
	except Exception:
		return None

def _supports_batch() -> bool:
	"""Conservatively detect if model supports batching on both inputs."""
	face_swapper = get_inference_pool().get('face_swapper')
	try:
		inputs = face_swapper.get_inputs()
	except Exception:
		return False
	batch_ok = True
	for i in inputs:
		shape = list(i.shape or [])
		if not shape:
			continue
		b = shape[0]
		# Dynamic or unknown dims are represented by None or strings in ORT
		if isinstance(b, int) and b == 1:
			batch_ok = False
	return batch_ok

def _prepare_crop_frame_batch(frames : List[VisionFrame], as_gpu : bool = False) -> Any:
	if as_gpu and _HAS_CUPY:
		return _prepare_crop_frame_batch_gpu(frames)
	return _prepare_crop_frame_batch_cpu(frames)



def _prepare_crop_frame_batch_cpu(frames : List[VisionFrame]) -> numpy.ndarray:
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')
	arr = numpy.stack([(f[:, :, ::-1] / 255.0) for f in frames], axis = 0)
	arr = (arr - model_mean) / model_standard_deviation
	arr = arr.transpose(0, 3, 1, 2).astype(numpy.float32)
	return arr



def _prepare_crop_frame_batch_gpu(frames : List[VisionFrame]) -> "cp.ndarray":
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')
	mean_gpu, std_gpu, inv_std_gpu = _get_model_stats_gpu(model_mean, model_standard_deviation)
	arr_gpu = cp.stack([cp.asarray(frame, dtype = cp.float32) for frame in frames], axis = 0)
	arr_gpu = arr_gpu[:, :, :, ::-1] * (1.0 / 255.0)
	arr_gpu = (arr_gpu - mean_gpu) * inv_std_gpu
	arr_gpu = cp.transpose(arr_gpu, (0, 3, 1, 2)).astype(cp.float32, copy = False)
	return arr_gpu



def _get_model_stats_gpu(model_mean : Any, model_standard_deviation : Any) -> Tuple["cp.ndarray", "cp.ndarray", "cp.ndarray"]:
	key = tuple(map(float, model_mean)) + tuple(map(float, model_standard_deviation))
	stats = _GPU_MODEL_STATS.get(key)
	if stats is None:
		mean_gpu = cp.asarray(model_mean, dtype = cp.float32).reshape(1, 1, 1, 3)
		std_gpu = cp.asarray(model_standard_deviation, dtype = cp.float32).reshape(1, 1, 1, 3)
		inv_std_gpu = 1.0 / std_gpu
		stats = (mean_gpu, std_gpu, inv_std_gpu)
		_GPU_MODEL_STATS[key] = stats
	return stats



def _normalize_crop_frame_batch(batch : Any) -> List[VisionFrame]:
	model_type = get_model_options().get('type')
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')

	if _HAS_CUPY and isinstance(batch, cp.ndarray):
		arr_gpu = cp.transpose(batch, (0, 2, 3, 1))
		if model_type in [ 'ghost', 'hififace', 'hyperswap', 'uniface' ]:
			mean_gpu, std_gpu, _ = _get_model_stats_gpu(model_mean, model_standard_deviation)
			arr_gpu = arr_gpu * std_gpu + mean_gpu
		arr_gpu = cp.clip(arr_gpu, 0.0, 1.0)
		arr_gpu = cp.flip(arr_gpu, axis = -1) * 255.0
		arr_np = cp.asnumpy(arr_gpu)
		return [arr_np[i] for i in range(arr_np.shape[0])]

	arr_np = batch.transpose(0, 2, 3, 1)
	if model_type in [ 'ghost', 'hififace', 'hyperswap', 'uniface' ]:
		arr_np = arr_np * model_standard_deviation + model_mean
	arr_np = arr_np.clip(0, 1)
	arr_np = (arr_np[:, :, :, ::-1] * 255.0)
	return [arr_np[i] for i in range(arr_np.shape[0])]

def swap_faces_batch(source_face : Face, target_faces : List[Face], target_vision_frame : VisionFrame, temp_vision_frame : VisionFrame) -> VisionFrame:
	"""Batch all crops (including pixel boost tiles) across all faces into one ONNX run."""
	if not target_faces:
		return temp_vision_frame
	model_options = get_model_options()
	model_template = model_options.get('template')
	model_size = model_options.get('size')
	model_path = model_options.get('sources').get('face_swapper').get('path')
	pixel_boost_size = unpack_resolution(state_manager.get_item('face_swapper_pixel_boost'))
	pixel_boost_total = pixel_boost_size[0] // model_size[0]

	# Record face count for dynamic heuristic
	_record_face_count_for_heuristic(len(target_faces))

	# Prepare per-tile inputs
	tile_inputs : List[VisionFrame] = []
	map_items : List[Dict[str, Any]] = []  # map tile index to face index and bookkeeping
	box_occ_masks : Dict[int, List[numpy.ndarray]] = {}

	# Precompute source input (frame or base embedding)
	model_type = get_model_options().get('type')
	base_source_emb : Optional[Embedding] = None
	source_frame_tensor : Optional[numpy.ndarray] = None
	if model_type in [ 'blendswap', 'uniface' ]:
		source_frame_tensor = prepare_source_frame(source_face)  # shape (1,C,H,W)
	else:
		base_source_emb = _get_cached_source_embedding(source_face)

	# Scale faces to temp_vision_frame size for correct warping
	scaled_faces : List[Face] = [scale_face(tf, target_vision_frame, temp_vision_frame) for tf in target_faces]

	# The common single-face / no-tiling case gains nothing from the batch path and
	# pays extra Cupy/IO-binding setup cost, so keep the lean sequential swap.
	if len(scaled_faces) == 1 and pixel_boost_total <= 1:
		return swap_face(source_face, scaled_faces[0], temp_vision_frame)

	for face_index, tface in enumerate(scaled_faces):
		crop_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, tface.landmark_set.get('5/68'), model_template, pixel_boost_size)
		# Precompute content-agnostic masks
		masks = []
		if 'box' in state_manager.get_item('face_mask_types'):
			masks.append(create_box_mask(crop_frame, state_manager.get_item('face_mask_blur'), state_manager.get_item('face_mask_padding')))
		if 'occlusion' in state_manager.get_item('face_mask_types'):
			masks.append(create_occlusion_mask(crop_frame))
		box_occ_masks[face_index] = masks

		# Pixel boost tiles
		tiles = implode_pixel_boost(crop_frame, pixel_boost_total, model_size)
		# Prepare tiles for model input
		for tile_idx in range(tiles.shape[0]):
			tile_inputs.append(tiles[tile_idx])
			map_items.append({'face_index': face_index, 'affine': affine_matrix})

		# If nothing to process, return
		if not tile_inputs:
			return temp_vision_frame

		# Heuristic: on non-GPU providers, small face counts without tiling favor sequential path
		providers = state_manager.get_item('execution_providers') or []
		providers = [str(p).lower() for p in providers]
		is_gpu = any(p in ('cuda', 'tensorrt') for p in providers)
		batching_mode = state_manager.get_item('face_swapper_batching') or 'auto'
		prefer_seq = (not is_gpu) and (_heuristic_state.get('decided') and _heuristic_state.get('prefer_sequential'))
		if batching_mode == 'never':
			prefer_seq = True
		if batching_mode == 'always':
			prefer_seq = False
		if (not is_gpu) and ((len(target_faces) <= 2 and pixel_boost_total <= 1) or prefer_seq):
			# Run original sequential per-face path (fastest for CPU/CoreML single-face cases)
			seq_start = time()
			for sf in [scale_face(tf, target_vision_frame, temp_vision_frame) for tf in target_faces]:
				temp_vision_frame = swap_face(source_face, sf, temp_vision_frame)
			seq_total = (time() - seq_start) * 1000.0
			# per-frame verbose logs removed for speed at info level
			return temp_vision_frame

	# Build batched inputs for ONNX
	face_swapper = get_inference_pool().get('face_swapper')

	# Compose per-tile source inputs (balance if needed)
	source_inputs_batch : Optional[numpy.ndarray] = None
	if model_type in [ 'blendswap', 'uniface' ] and source_frame_tensor is not None:
		# Repeat source frame per tile
		source_inputs_batch = numpy.repeat(source_frame_tensor, repeats=len(tile_inputs), axis=0)
	else:
		# Embedding-based models: balance once per face, then repeat per tile
		per_face_src : List[numpy.ndarray] = []
		for sf in scaled_faces:
			src = prepare_source_embedding(source_face) if base_source_emb is None else base_source_emb
			per_face_src.append(balance_source_embedding(src, sf.embedding))
		# map tiles -> face embeddings
		emb_list : List[numpy.ndarray] = []
		for mi in map_items:
			fi = mi['face_index']
			emb_list.append(per_face_src[fi])
		source_inputs_batch = numpy.vstack(emb_list).astype(numpy.float32, copy = False)

	# Prepare target batch (CPU/GPU aware)
	target_inputs_batch_cpu : Optional[numpy.ndarray] = None
	target_inputs_batch_gpu : Optional['cp.ndarray'] = None

	# Detect batch capability; if unsupported, fallback per-tile
	batched = _supports_batch()
	outputs_batch : Optional[Any] = None
	use_trt = False

	# Attempt TensorRT execution when available and requested
	if batched and tensorrt_runner.is_available() and state_manager.get_item('face_swapper_use_trt') and 'tensorrt' in providers and _HAS_CUPY:
		if target_inputs_batch_gpu is None:
			target_inputs_batch_gpu = _prepare_crop_frame_batch(tile_inputs, as_gpu = True)
		src_cu = cp.asarray(source_inputs_batch, dtype = cp.float32)
		trt_limit = state_manager.get_item('face_swapper_trt_max_batch') or 64
		try:
			tensorrt_runner.set_max_batch_limit(int(trt_limit))
		except Exception:
			pass
		batch_total = len(tile_inputs)
		engine_batch = max(1, tensorrt_runner.canonicalize_batch_size(batch_total))
		source_engine_shape = (engine_batch, *source_inputs_batch.shape[1:])
		target_engine_shape = (engine_batch, *target_inputs_batch_gpu.shape[1:])
		runner = tensorrt_runner.get_runner(model_path, source_engine_shape, target_engine_shape, engine_batch)
		if runner:
			use_trt = True
			outputs_parts : List["cp.ndarray"] = []
			cursor = 0
			while cursor < batch_total:
				end = min(cursor + runner.max_batch, batch_total)
				src_slice = src_cu[cursor:end]
				tgt_slice = target_inputs_batch_gpu[cursor:end]
				run_out = runner.run(src_slice, tgt_slice)
				outputs_parts.append(run_out)
				cursor = end
			if outputs_parts:
				outputs_batch = cp.concatenate(outputs_parts, axis = 0)

	if batched and not use_trt:
		use_iobinding = _HAS_CUPY and ('cuda' in state_manager.get_item('execution_providers'))
		if use_iobinding:
			try:
				if target_inputs_batch_gpu is None:
					target_inputs_batch_gpu = _prepare_crop_frame_batch(tile_inputs, as_gpu = True)
				device_id = int(get_first(state_manager.get_item('execution_device_ids')))
				io_binding = face_swapper.io_binding()
				src_cu = cp.asarray(source_inputs_batch, dtype = cp.float32)
				tgt_cu = target_inputs_batch_gpu
				N, C, H, W = tgt_cu.shape
				out_cu = cp.empty((N, C, H, W), dtype = cp.float32)
				inputs_by_name = { i.name: i for i in face_swapper.get_inputs() }
				outputs_by_name = { o.name: o for o in face_swapper.get_outputs() }
				src_name = 'source' if 'source' in inputs_by_name else list(inputs_by_name.keys())[0]
				tgt_name = 'target' if 'target' in inputs_by_name else list(inputs_by_name.keys())[1]
				out_name = list(outputs_by_name.keys())[0]
				io_binding.bind_input(name = src_name, device_type = 'cuda', device_id = device_id, element_type = numpy.float32, shape = tuple(source_inputs_batch.shape), buffer_ptr = src_cu.data.ptr)
				io_binding.bind_input(name = tgt_name, device_type = 'cuda', device_id = device_id, element_type = numpy.float32, shape = tuple(tgt_cu.shape), buffer_ptr = tgt_cu.data.ptr)
				io_binding.bind_output(name = out_name, device_type = 'cuda', device_id = device_id, shape = (N, C, H, W), buffer_ptr = out_cu.data.ptr)
				t_run_start = time()
				with conditional_thread_semaphore():
					face_swapper.run_with_iobinding(io_binding)
				t_run_end = time()
				outputs_batch = out_cu
			except Exception:
				use_iobinding = False
				target_inputs_batch_cpu = _prepare_crop_frame_batch(tile_inputs)
		if not use_iobinding:
			if target_inputs_batch_cpu is None:
				target_inputs_batch_cpu = _prepare_crop_frame_batch(tile_inputs)
			face_swapper_inputs = {}
			for face_swapper_input in face_swapper.get_inputs():
				if face_swapper_input.name == 'source':
					face_swapper_inputs[face_swapper_input.name] = source_inputs_batch
				if face_swapper_input.name == 'target':
					face_swapper_inputs[face_swapper_input.name] = target_inputs_batch_cpu
			t_run_start = time()
			with conditional_thread_semaphore():
				outputs_batch = face_swapper.run(None, face_swapper_inputs)[0]
			t_run_end = time()
	else:
		# Fallback: parallelize by face with precomputed source, then paste sequentially
		prepared_by_face = [ _build_prepared_source_for_face(source_face, sf) for sf in scaled_faces ]
		results : Dict[int, Tuple[VisionFrame, numpy.ndarray, numpy.ndarray]] = {}
		max_workers = max(1, state_manager.get_item('execution_thread_count') or 4)
		with ThreadPoolExecutor(max_workers=max_workers) as ex:
			futs = []
			for fi, sf in enumerate(scaled_faces):
				futs.append((fi, ex.submit(_swap_face_to_layers, prepared_by_face[fi], sf, temp_vision_frame)))
			for fi, fut in futs:
				results[fi] = fut.result()
		# Paste back in stable order (by face index)
		for fi in range(len(scaled_faces)):
			crop_swapped, crop_mask, affine_matrix = results[fi]
			temp_vision_frame = paste_back(temp_vision_frame, crop_swapped, crop_mask, affine_matrix)
		return temp_vision_frame

	if outputs_batch is None:
		return temp_vision_frame

	# Post-process outputs and paste back face-by-face
	# Convert model outputs to HWC per-tile
	tiles_out : List[VisionFrame] = _normalize_crop_frame_batch(outputs_batch)

	# Group tiles per face and paste
	per_face_tiles : Dict[int, List[VisionFrame]] = {}
	for tile, mi in zip(tiles_out, map_items):
		fi = mi['face_index']
		per_face_tiles.setdefault(fi, []).append(tile)

	paste_start = time()
	for fi, tiles in per_face_tiles.items():
		# Reassemble boosted crop
		crop_swapped = explode_pixel_boost(tiles, pixel_boost_total, model_size, pixel_boost_size)
		# Compose masks: box/occlusion + dynamic area/region
		masks = list(box_occ_masks.get(fi, []))
		# Area mask depends on transformed 68-landmarks
		# Recompute affine for this face from first tile's map item
		affine_matrix = None
		for mi in map_items:
			if mi['face_index'] == fi:
				affine_matrix = mi['affine']
				break
		if 'area' in state_manager.get_item('face_mask_types') and affine_matrix is not None:
			face_landmark_68 = scaled_faces[fi].landmark_set.get('68')
			face_landmark_68 = cv2.transform(face_landmark_68.reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
			masks.append(create_area_mask(crop_swapped, face_landmark_68, state_manager.get_item('face_mask_areas')))
		if 'region' in state_manager.get_item('face_mask_types'):
			masks.append(create_region_mask(crop_swapped, state_manager.get_item('face_mask_regions')))
		if masks:
			crop_mask = numpy.minimum.reduce(masks).clip(0, 1)
		else:
			crop_mask = numpy.ones(crop_swapped.shape[:2], dtype=numpy.float32)
			# Paste back
			affine_matrix = affine_matrix if affine_matrix is not None else numpy.eye(2, 3, dtype=numpy.float32)
			temp_vision_frame = paste_back(temp_vision_frame, crop_swapped, crop_mask, affine_matrix)
	paste_end = time()

	faces_batched = len(scaled_faces)
	tiles_batched = len(map_items)
	onnx_ms = ((t_run_end - t_run_start) * 1000.0) if 't_run_start' in locals() and 't_run_end' in locals() else -1.0
	paste_ms = (paste_end - paste_start) * 1000.0
	# per-frame verbose logs removed for speed at info level
	return temp_vision_frame


def swap_face(source_face : Face, target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_template = get_model_options().get('template')
	model_size = get_model_options().get('size')
	pixel_boost_size = unpack_resolution(state_manager.get_item('face_swapper_pixel_boost'))
	pixel_boost_total = pixel_boost_size[0] // model_size[0]
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), model_template, pixel_boost_size)
	temp_vision_frames = []
	crop_masks = []

	if 'box' in state_manager.get_item('face_mask_types'):
		box_mask = create_box_mask(crop_vision_frame, state_manager.get_item('face_mask_blur'), state_manager.get_item('face_mask_padding'))
		crop_masks.append(box_mask)

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	# Fast path when pixel boost is 1: avoid reshape/loop overhead
	if pixel_boost_total <= 1:
		pixel_boost_vision_frame = prepare_crop_frame(crop_vision_frame)
		pixel_boost_vision_frame = forward_swap_face(source_face, target_face, pixel_boost_vision_frame)
		crop_vision_frame = normalize_crop_frame(pixel_boost_vision_frame)
	else:
		pixel_boost_vision_frames = implode_pixel_boost(crop_vision_frame, pixel_boost_total, model_size)
		for pixel_boost_vision_frame in pixel_boost_vision_frames:
			pixel_boost_vision_frame = prepare_crop_frame(pixel_boost_vision_frame)
			pixel_boost_vision_frame = forward_swap_face(source_face, target_face, pixel_boost_vision_frame)
			pixel_boost_vision_frame = normalize_crop_frame(pixel_boost_vision_frame)
			temp_vision_frames.append(pixel_boost_vision_frame)
		crop_vision_frame = explode_pixel_boost(temp_vision_frames, pixel_boost_total, model_size, pixel_boost_size)

	if 'area' in state_manager.get_item('face_mask_types'):
		face_landmark_68 = cv2.transform(target_face.landmark_set.get('68').reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
		area_mask = create_area_mask(crop_vision_frame, face_landmark_68, state_manager.get_item('face_mask_areas'))
		crop_masks.append(area_mask)

	if 'region' in state_manager.get_item('face_mask_types'):
		region_mask = create_region_mask(crop_vision_frame, state_manager.get_item('face_mask_regions'))
		crop_masks.append(region_mask)

	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	return paste_vision_frame


def forward_swap_face(source_face : Face, target_face : Face, crop_vision_frame : VisionFrame) -> VisionFrame:
	face_swapper = get_inference_pool().get('face_swapper')
	model_type = get_model_options().get('type')
	face_swapper_inputs = {}

	if is_macos() and has_execution_provider('coreml') and model_type in [ 'ghost', 'uniface' ]:
		face_swapper.set_providers([ facefusion.choices.execution_provider_set.get('cpu') ])

	for face_swapper_input in face_swapper.get_inputs():
		if face_swapper_input.name == 'source':
			if model_type in [ 'blendswap', 'uniface' ]:
				face_swapper_inputs[face_swapper_input.name] = prepare_source_frame(source_face)
			else:
				source_embedding = prepare_source_embedding(source_face)
				source_embedding = balance_source_embedding(source_embedding, target_face.embedding)
				face_swapper_inputs[face_swapper_input.name] = source_embedding
		if face_swapper_input.name == 'target':
			face_swapper_inputs[face_swapper_input.name] = crop_vision_frame

	with conditional_thread_semaphore():
		crop_vision_frame = face_swapper.run(None, face_swapper_inputs)[0][0]

	return crop_vision_frame


def forward_convert_embedding(face_embedding : Embedding) -> Embedding:
	embedding_converter = get_inference_pool().get('embedding_converter')

	with conditional_thread_semaphore():
		face_embedding = embedding_converter.run(None,
		{
			'input': face_embedding
		})[0]

	return face_embedding


def prepare_source_frame(source_face : Face) -> VisionFrame:
	model_type = get_model_options().get('type')
	source_vision_frame = read_static_image(get_first(state_manager.get_item('source_paths')))

	if model_type == 'blendswap':
		source_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'arcface_112_v2', (112, 112))

	if model_type == 'uniface':
		source_vision_frame, _ = warp_face_by_face_landmark_5(source_vision_frame, source_face.landmark_set.get('5/68'), 'ffhq_512', (256, 256))

	source_vision_frame = source_vision_frame[:, :, ::-1] / 255.0
	source_vision_frame = source_vision_frame.transpose(2, 0, 1)
	source_vision_frame = numpy.expand_dims(source_vision_frame, axis = 0).astype(numpy.float32)
	return source_vision_frame


def prepare_source_embedding(source_face : Face) -> Embedding:
	model_type = get_model_options().get('type')

	if model_type == 'ghost':
		source_embedding = source_face.embedding.reshape(-1, 512)
		source_embedding, _ = convert_source_embedding(source_embedding)
		source_embedding = source_embedding.reshape(1, -1)
		return source_embedding

	if model_type == 'hyperswap':
		source_embedding = source_face.embedding_norm.reshape((1, -1))
		return source_embedding

	if model_type == 'inswapper':
		model_path = get_model_options().get('sources').get('face_swapper').get('path')
		model_initializer = get_static_model_initializer(model_path)
		source_embedding = source_face.embedding.reshape((1, -1))
		source_embedding = numpy.dot(source_embedding, model_initializer) / numpy.linalg.norm(source_embedding)
		return source_embedding

	source_embedding = source_face.embedding.reshape(-1, 512)
	_, source_embedding_norm = convert_source_embedding(source_embedding)
	source_embedding = source_embedding_norm.reshape(1, -1)
	return source_embedding


def balance_source_embedding(source_embedding : Embedding, target_embedding : Embedding) -> Embedding:
	model_type = get_model_options().get('type')
	face_swapper_weight = state_manager.get_item('face_swapper_weight')
	face_swapper_weight = numpy.interp(face_swapper_weight, [ 0, 1 ], [ 0.35, -0.35 ]).astype(numpy.float32)

	if model_type in [ 'hififace', 'hyperswap', 'inswapper', 'simswap' ]:
		target_embedding = target_embedding / numpy.linalg.norm(target_embedding)

	source_embedding = source_embedding.reshape(1, -1)
	target_embedding = target_embedding.reshape(1, -1)
	source_embedding = source_embedding * (1 - face_swapper_weight) + target_embedding * face_swapper_weight
	return source_embedding


def convert_source_embedding(source_embedding : Embedding) -> Tuple[Embedding, Embedding]:
	source_embedding = forward_convert_embedding(source_embedding)
	source_embedding = source_embedding.ravel()
	source_embedding_norm = source_embedding / numpy.linalg.norm(source_embedding)
	return source_embedding, source_embedding_norm


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')

	crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
	crop_vision_frame = (crop_vision_frame - model_mean) / model_standard_deviation
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 1)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0).astype(numpy.float32)
	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	model_type = get_model_options().get('type')
	model_mean = get_model_options().get('mean')
	model_standard_deviation = get_model_options().get('standard_deviation')

	crop_vision_frame = crop_vision_frame.transpose(1, 2, 0)

	if model_type in [ 'ghost', 'hififace', 'hyperswap', 'uniface' ]:
		crop_vision_frame = crop_vision_frame * model_standard_deviation + model_mean

	crop_vision_frame = crop_vision_frame.clip(0, 1)
	crop_vision_frame = crop_vision_frame[:, :, ::-1] * 255
	return crop_vision_frame


def extract_source_face(source_vision_frames : List[VisionFrame]) -> Optional[Face]:
	source_faces = []

	if source_vision_frames:
		for source_vision_frame in source_vision_frames:
			temp_faces = get_many_faces([source_vision_frame], use_tracking = False)
			temp_faces = sort_faces_by_order(temp_faces, 'large-small')

			if temp_faces:
				source_faces.append(get_first(temp_faces))

	return get_average_face(source_faces)


def process_frame(inputs : FaceSwapperInputs) -> VisionFrame:
    reference_vision_frame = inputs.get('reference_vision_frame')
    source_vision_frames = inputs.get('source_vision_frames')
    target_vision_frame = inputs.get('target_vision_frame')
    temp_vision_frame = inputs.get('temp_vision_frame')
    # Cache source face across frames for multi-thread speed
    source_face = _get_cached_source_face(source_vision_frames)
    target_faces = select_faces(reference_vision_frame, target_vision_frame)

    if source_face and target_faces:
        # Batch all faces + pixel boost tiles through a single ONNX run
        temp_vision_frame = swap_faces_batch(source_face, target_faces, target_vision_frame, temp_vision_frame)

    return temp_vision_frame
