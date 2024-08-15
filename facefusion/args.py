from facefusion import state_manager
from facefusion.filesystem import is_image, is_video, list_directory
from facefusion.jobs import job_store
from facefusion.normalizer import normalize_fps, normalize_padding
from facefusion.processors.core import load_processor_module
from facefusion.typing import Args
from facefusion.vision import create_image_resolutions, create_video_resolutions, detect_image_resolution, detect_video_fps, detect_video_resolution, pack_resolution


def reduce_step_args(args : Args) -> Args:
	step_args =\
	{
		key: args[key] for key in args if key in job_store.get_step_keys()
	}
	return step_args


def collect_step_args() -> Args:
	step_args =\
	{
		key: state_manager.get_item(key) for key in job_store.get_step_keys() #type:ignore[arg-type]
	}
	return step_args


def collect_job_args() -> Args:
	job_args =\
	{
		key: state_manager.get_item(key) for key in job_store.get_job_keys() #type:ignore[arg-type]
	}
	return job_args


def apply_args(args : Args) -> None:
	# general
	state_manager.init_item('command', args.get('command'))
	# paths
	state_manager.init_item('jobs_path', args.get('jobs_path'))
	state_manager.init_item('source_paths', args.get('source_paths'))
	state_manager.init_item('target_path', args.get('target_path'))
	state_manager.init_item('output_path', args.get('output_path'))
	# face analyser
	state_manager.init_item('face_detector_model', args.get('face_detector_model'))
	state_manager.init_item('face_detector_size', args.get('face_detector_size'))
	state_manager.init_item('face_detector_angles', args.get('face_detector_angles'))
	state_manager.init_item('face_detector_score', args.get('face_detector_score'))
	state_manager.init_item('face_landmarker_model', args.get('face_landmarker_model'))
	state_manager.init_item('face_landmarker_score', args.get('face_landmarker_score'))
	# face selector
	state_manager.init_item('face_selector_mode', args.get('face_selector_mode'))
	state_manager.init_item('face_selector_order', args.get('face_selector_order'))
	state_manager.init_item('face_selector_age', args.get('face_selector_age'))
	state_manager.init_item('face_selector_gender', args.get('face_selector_gender'))
	state_manager.init_item('reference_face_position', args.get('reference_face_position'))
	state_manager.init_item('reference_face_distance', args.get('reference_face_distance'))
	state_manager.init_item('reference_frame_number', args.get('reference_frame_number'))
	# face masker
	state_manager.init_item('face_mask_types', args.get('face_mask_types'))
	state_manager.init_item('face_mask_blur', args.get('face_mask_blur'))
	state_manager.init_item('face_mask_padding', normalize_padding(args.get('face_mask_padding')))
	state_manager.init_item('face_mask_regions', args.get('face_mask_regions'))
	# frame extraction
	state_manager.init_item('trim_frame_start', args.get('trim_frame_start'))
	state_manager.init_item('trim_frame_end', args.get('trim_frame_end'))
	state_manager.init_item('temp_frame_format', args.get('temp_frame_format'))
	state_manager.init_item('keep_temp', args.get('keep_temp'))
	# output creation
	state_manager.init_item('output_image_quality', args.get('output_image_quality'))
	if is_image(args.get('target_path')):
		output_image_resolution = detect_image_resolution(args.get('target_path'))
		output_image_resolutions = create_image_resolutions(output_image_resolution)
		if args.get('output_image_resolution') in output_image_resolutions:
			state_manager.init_item('output_image_resolution', args.get('output_image_resolution'))
		else:
			state_manager.init_item('output_image_resolution', pack_resolution(output_image_resolution))
	state_manager.init_item('output_audio_encoder', args.get('output_audio_encoder'))
	state_manager.init_item('output_video_encoder', args.get('output_video_encoder'))
	state_manager.init_item('output_video_preset', args.get('output_video_preset'))
	state_manager.init_item('output_video_quality', args.get('output_video_quality'))
	if is_video(args.get('target_path')):
		output_video_resolution = detect_video_resolution(args.get('target_path'))
		output_video_resolutions = create_video_resolutions(output_video_resolution)
		if args.get('output_video_resolution') in output_video_resolutions:
			state_manager.init_item('output_video_resolution', args.get('output_video_resolution'))
		else:
			state_manager.init_item('output_video_resolution', pack_resolution(output_video_resolution))
	if args.get('output_video_fps') or is_video(args.get('target_path')):
		output_video_fps = normalize_fps(args.get('output_video_fps')) or detect_video_fps(args.get('target_path'))
		state_manager.init_item('output_video_fps', output_video_fps)
	state_manager.init_item('skip_audio', args.get('skip_audio'))
	# processors
	available_processors = list_directory('facefusion/processors/modules')
	state_manager.init_item('processors', args.get('processors'))
	for processor in available_processors:
		processor_module = load_processor_module(processor)
		processor_module.apply_args(args)
	# uis
	if args.get('command') == 'run':
		state_manager.init_item('open_browser', args.get('open_browser'))
		state_manager.init_item('ui_layouts', args.get('ui_layouts'))
		state_manager.init_item('ui_workflow', args.get('ui_workflow'))
	# execution
	state_manager.init_item('execution_device_id', args.get('execution_device_id'))
	state_manager.init_item('execution_providers', args.get('execution_providers'))
	state_manager.init_item('execution_thread_count', args.get('execution_thread_count'))
	state_manager.init_item('execution_queue_count', args.get('execution_queue_count'))
	# memory
	state_manager.init_item('video_memory_strategy', args.get('video_memory_strategy'))
	state_manager.init_item('system_memory_limit', args.get('system_memory_limit'))
	# misc
	state_manager.init_item('skip_download', args.get('skip_download'))
	state_manager.init_item('log_level', args.get('log_level'))
	# job
	state_manager.init_item('job_id', args.get('job_id'))
	state_manager.init_item('job_status', args.get('job_status'))
	state_manager.init_item('step_index', args.get('step_index'))
