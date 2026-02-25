from typing import Union

from facefusion.capability_store import get_api_arguments, get_cli_arguments, get_sys_arguments
from facefusion.filesystem import get_file_name, is_video, resolve_file_paths
from facefusion.normalizer import normalize_fps, normalize_space
from facefusion.processors.core import get_processors_modules
from facefusion.processors.types import ProcessorState
from facefusion.types import ApplyStateItem, Args, State
from facefusion.vision import detect_video_fps


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('command', args.get('command'))
	apply_state_item('workflow', args.get('workflow'))
	apply_state_item('temp_path', args.get('temp_path'))
	apply_state_item('jobs_path', args.get('jobs_path'))
	apply_state_item('source_paths', args.get('source_paths'))
	apply_state_item('target_path', args.get('target_path'))
	apply_state_item('output_path', args.get('output_path'))
	apply_state_item('source_pattern', args.get('source_pattern'))
	apply_state_item('target_pattern', args.get('target_pattern'))
	apply_state_item('output_pattern', args.get('output_pattern'))
	apply_state_item('face_detector_model', args.get('face_detector_model'))
	apply_state_item('face_detector_size', args.get('face_detector_size'))
	apply_state_item('face_detector_margin', normalize_space(args.get('face_detector_margin')))
	apply_state_item('face_detector_angles', args.get('face_detector_angles'))
	apply_state_item('face_detector_score', args.get('face_detector_score'))
	apply_state_item('face_landmarker_model', args.get('face_landmarker_model'))
	apply_state_item('face_landmarker_score', args.get('face_landmarker_score'))
	apply_state_item('face_selector_mode', args.get('face_selector_mode'))
	apply_state_item('face_selector_order', args.get('face_selector_order'))
	apply_state_item('face_selector_age_start', args.get('face_selector_age_start'))
	apply_state_item('face_selector_age_end', args.get('face_selector_age_end'))
	apply_state_item('face_selector_gender', args.get('face_selector_gender'))
	apply_state_item('face_selector_race', args.get('face_selector_race'))
	apply_state_item('reference_face_position', args.get('reference_face_position'))
	apply_state_item('reference_face_distance', args.get('reference_face_distance'))
	apply_state_item('reference_frame_number', args.get('reference_frame_number'))
	apply_state_item('face_occluder_model', args.get('face_occluder_model'))
	apply_state_item('face_parser_model', args.get('face_parser_model'))
	apply_state_item('face_mask_types', args.get('face_mask_types'))
	apply_state_item('face_mask_areas', args.get('face_mask_areas'))
	apply_state_item('face_mask_regions', args.get('face_mask_regions'))
	apply_state_item('face_mask_blur', args.get('face_mask_blur'))
	apply_state_item('face_mask_padding', normalize_space(args.get('face_mask_padding')))
	apply_state_item('voice_extractor_model', args.get('voice_extractor_model'))
	apply_state_item('trim_frame_start', args.get('trim_frame_start'))
	apply_state_item('trim_frame_end', args.get('trim_frame_end'))
	apply_state_item('temp_frame_format', args.get('temp_frame_format'))
	apply_state_item('output_image_quality', args.get('output_image_quality'))
	apply_state_item('output_image_scale', args.get('output_image_scale'))
	apply_state_item('output_audio_encoder', args.get('output_audio_encoder'))
	apply_state_item('output_audio_quality', args.get('output_audio_quality'))
	apply_state_item('output_audio_volume', args.get('output_audio_volume'))
	apply_state_item('output_video_encoder', args.get('output_video_encoder'))
	apply_state_item('output_video_preset', args.get('output_video_preset'))
	apply_state_item('output_video_quality', args.get('output_video_quality'))
	apply_state_item('output_video_scale', args.get('output_video_scale'))

	if args.get('output_video_fps') or is_video(args.get('target_path')):
		output_video_fps = normalize_fps(args.get('output_video_fps')) or detect_video_fps(args.get('target_path'))
		apply_state_item('output_video_fps', output_video_fps)

	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/processors/modules') ]
	apply_state_item('processors', args.get('processors'))

	for processor_module in get_processors_modules(available_processors):
		processor_module.apply_args(args, apply_state_item)

	apply_state_item('execution_device_ids', args.get('execution_device_ids'))
	apply_state_item('execution_providers', args.get('execution_providers'))
	apply_state_item('execution_thread_count', args.get('execution_thread_count'))
	apply_state_item('download_providers', args.get('download_providers'))
	apply_state_item('download_scope', args.get('download_scope'))
	apply_state_item('benchmark_mode', args.get('benchmark_mode'))
	apply_state_item('benchmark_resolutions', args.get('benchmark_resolutions'))
	apply_state_item('benchmark_cycle_count', args.get('benchmark_cycle_count'))
	apply_state_item('api_host', args.get('api_host'))
	apply_state_item('api_port', args.get('api_port'))
	apply_state_item('video_memory_strategy', args.get('video_memory_strategy'))
	apply_state_item('log_level', args.get('log_level'))
	apply_state_item('halt_on_error', args.get('halt_on_error'))
	apply_state_item('job_id', args.get('job_id'))
	apply_state_item('job_status', args.get('job_status'))
	apply_state_item('step_index', args.get('step_index'))


def extract_api_args(state : Union[State, ProcessorState]) -> Args:
	api_args =\
	{
		key: state.get(key) for key in state if key in get_api_arguments()
	}
	return api_args


def extract_cli_args(state : Union[State, ProcessorState]) -> Args:
	cli_args =\
	{
		key: state.get(key) for key in state if key in get_cli_arguments()
	}
	return cli_args


def extract_sys_args(state : Union[State, ProcessorState]) -> Args:
	sys_args =\
	{
		key: state.get(key) for key in state if key in get_sys_arguments()
	}
	return sys_args


def extract_step_args(state : Union[State, ProcessorState]) -> Args:
	step_args =\
	{
		key: state.get(key) for key in state if key in get_cli_arguments() and key not in get_sys_arguments()
	}
	return step_args


def filter_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args.get(key) for key in args if key in get_cli_arguments() and key not in get_sys_arguments()
	}
	return step_args
