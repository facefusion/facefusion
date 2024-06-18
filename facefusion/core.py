import os

os.environ['OMP_NUM_THREADS'] = '1'

import signal
import sys
import warnings
import shutil
import numpy
import onnxruntime
from time import sleep, time
from argparse import ArgumentParser, HelpFormatter

import facefusion.choices
import facefusion.globals
from facefusion.typing import ErrorCode, Args
from facefusion import face_analyser, face_masker, content_analyser, config, process_manager, metadata, logger, voice_extractor, wording
from facefusion.jobs import job_manager, job_runner, job_store, job_helper
from facefusion.program_helper import validate_args, reduce_args, update_args, import_globals
from facefusion.face_analyser import get_one_face, get_average_face
from facefusion.face_store import get_reference_faces, append_reference_face
from facefusion.content_analyser import analyse_image, analyse_video
from facefusion.processors.frame.core import clear_frame_processors_modules, get_frame_processors_modules, load_frame_processor_module
from facefusion.exit_helper import hard_exit, conditional_exit, graceful_exit
from facefusion.common_helper import create_metavar, get_first, get_argument_value
from facefusion.execution import get_execution_provider_choices
from facefusion.normalizer import normalize_padding, normalize_fps
from facefusion.memory import limit_system_memory
from facefusion.statistics import conditional_log_statistics
from facefusion.download import conditional_download
from facefusion.filesystem import is_image, is_video, filter_audio_paths, resolve_relative_path, list_directory
from facefusion.temp_helper import get_temp_frame_paths, get_temp_file_path, create_temp_directory, move_temp_file, clear_temp_directory
from facefusion.ffmpeg import extract_frames, merge_video, copy_image, finalize_image, restore_audio, replace_audio
from facefusion.vision import read_image, read_static_images, detect_image_resolution, restrict_video_fps, create_image_resolutions, get_video_frame, detect_video_resolution, detect_video_fps, restrict_video_resolution, restrict_image_resolution, create_video_resolutions, pack_resolution, unpack_resolution
import facefusion.processors.frame

onnxruntime.set_default_logger_severity(3)
warnings.filterwarnings('ignore', category = UserWarning, module = 'gradio')


def cli() -> None:
	signal.signal(signal.SIGINT, lambda signal_number, frame: graceful_exit(0))
	program = create_program()

	if validate_args(program):
		apply_args(program)
		logger.init(facefusion.globals.log_level)
		run(program)


def create_program() -> ArgumentParser:
	program = ArgumentParser(formatter_class = lambda prog: HelpFormatter(prog, max_help_position = 200), add_help = False)
	# general
	program.add_argument('-c', '--config-path', help = wording.get('help.config_path'), dest = 'config_path', default = 'facefusion.ini')
	apply_config_path(program)
	program.add_argument('-s', '--source-paths', help = wording.get('help.source_paths'), action = 'append', dest = 'source_paths', default = config.get_str_list('general.source_paths'))
	program.add_argument('-t', '--target-path', help = wording.get('help.target_path'), dest = 'target_path', default = config.get_str_value('general.target_path'))
	program.add_argument('-o', '--output-path', help = wording.get('help.output_path'), dest = 'output_path', default = config.get_str_value('general.output_path'))
	program.add_argument('-j', '--jobs-path', help = wording.get('help.jobs_path'), default = config.get_str_value('general.jobs_path', '.jobs'))
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	job_store.register_step_keys([ 'source_paths', 'target_path', 'output_path' ])
	# misc
	group_misc = program.add_argument_group('misc')
	group_misc.add_argument('--force-download', help = wording.get('help.force_download'), action = 'store_true', default = config.get_bool_value('misc.force_download'))
	group_misc.add_argument('--skip-download', help = wording.get('help.skip_download'), action = 'store_true', default = config.get_bool_value('misc.skip_download'))
	group_misc.add_argument('--headless', help = wording.get('help.headless'), action = 'store_true', default = config.get_bool_value('misc.headless'))
	group_misc.add_argument('--log-level', help = wording.get('help.log_level'), default = config.get_str_value('misc.log_level', 'info'), choices = logger.get_log_levels())
	job_store.register_job_keys([ 'skip_download', 'log_level' ])
	# execution
	execution_providers = get_execution_provider_choices()
	group_execution = program.add_argument_group('execution')
	group_execution.add_argument('--execution-device-id', help = wording.get('help.execution_device_id'), default = config.get_str_value('execution.face_detector_size', '0'))
	group_execution.add_argument('--execution-providers', help = wording.get('help.execution_providers').format(choices = ', '.join(execution_providers)), default = config.get_str_list('execution.execution_providers', 'cpu'), choices = execution_providers, nargs = '+', metavar = 'EXECUTION_PROVIDERS')
	group_execution.add_argument('--execution-thread-count', help = wording.get('help.execution_thread_count'), type = int, default = config.get_int_value('execution.execution_thread_count', '4'), choices = facefusion.choices.execution_thread_count_range, metavar = create_metavar(facefusion.choices.execution_thread_count_range))
	group_execution.add_argument('--execution-queue-count', help = wording.get('help.execution_queue_count'), type = int, default = config.get_int_value('execution.execution_queue_count', '1'), choices = facefusion.choices.execution_queue_count_range, metavar = create_metavar(facefusion.choices.execution_queue_count_range))
	job_store.register_job_keys([ 'execution_device_id', 'execution_providers', 'execution_thread_count', 'execution_queue_count' ])
	# memory
	group_memory = program.add_argument_group('memory')
	group_memory.add_argument('--video-memory-strategy', help = wording.get('help.video_memory_strategy'), default = config.get_str_value('memory.video_memory_strategy', 'strict'), choices = facefusion.choices.video_memory_strategies)
	group_memory.add_argument('--system-memory-limit', help = wording.get('help.system_memory_limit'), type = int, default = config.get_int_value('memory.system_memory_limit', '0'), choices = facefusion.choices.system_memory_limit_range, metavar = create_metavar(facefusion.choices.system_memory_limit_range))
	job_store.register_job_keys([ 'video_memory_strategy', 'system_memory_limit' ])
	# face analyser
	face_detector_model = get_argument_value('--face-detector-model') or 'yoloface'
	face_detector_size_choices = facefusion.choices.face_detector_set.get(face_detector_model) #type:ignore[call-overload]
	group_face_analyser = program.add_argument_group('face analyser')
	group_face_analyser.add_argument('--face-analyser-order', help = wording.get('help.face_analyser_order'), default = config.get_str_value('face_analyser.face_analyser_order', 'left-right'), choices = facefusion.choices.face_analyser_orders)
	group_face_analyser.add_argument('--face-analyser-age', help = wording.get('help.face_analyser_age'), default = config.get_str_value('face_analyser.face_analyser_age'), choices = facefusion.choices.face_analyser_ages)
	group_face_analyser.add_argument('--face-analyser-gender', help = wording.get('help.face_analyser_gender'), default = config.get_str_value('face_analyser.face_analyser_gender'), choices = facefusion.choices.face_analyser_genders)
	group_face_analyser.add_argument('--face-detector-model', help = wording.get('help.face_detector_model'), default = config.get_str_value('face_analyser.face_detector_model', 'yoloface'), choices = facefusion.choices.face_detector_set.keys())
	group_face_analyser.add_argument('--face-detector-size', help = wording.get('help.face_detector_size'), default = config.get_str_value('face_analyser.face_detector_size', '640x640'), choices = face_detector_size_choices, metavar = 'FACE_DETECTOR_SIZE')
	group_face_analyser.add_argument('--face-detector-score', help = wording.get('help.face_detector_score'), type = float, default = config.get_float_value('face_analyser.face_detector_score', '0.5'), choices = facefusion.choices.face_detector_score_range, metavar = create_metavar(facefusion.choices.face_detector_score_range))
	group_face_analyser.add_argument('--face-landmarker-score', help = wording.get('help.face_landmarker_score'), type = float, default = config.get_float_value('face_analyser.face_landmarker_score', '0.5'), choices = facefusion.choices.face_landmarker_score_range, metavar = create_metavar(facefusion.choices.face_landmarker_score_range))
	job_store.register_step_keys([ 'face_analyser_order', 'face_analyser_age', 'face_analyser_gender', 'face_detector_model', 'face_detector_size', 'face_detector_score', 'face_landmarker_score' ])
	# face selector
	group_face_selector = program.add_argument_group('face selector')
	group_face_selector.add_argument('--face-selector-mode', help = wording.get('help.face_selector_mode'), default = config.get_str_value('face_selector.face_selector_mode', 'reference'), choices = facefusion.choices.face_selector_modes)
	group_face_selector.add_argument('--reference-face-position', help = wording.get('help.reference_face_position'), type = int, default = config.get_int_value('face_selector.reference_face_position', '0'))
	group_face_selector.add_argument('--reference-face-distance', help = wording.get('help.reference_face_distance'), type = float, default = config.get_float_value('face_selector.reference_face_distance', '0.6'), choices = facefusion.choices.reference_face_distance_range, metavar = create_metavar(facefusion.choices.reference_face_distance_range))
	group_face_selector.add_argument('--reference-frame-number', help = wording.get('help.reference_frame_number'), type = int, default = config.get_int_value('face_selector.reference_frame_number', '0'))
	job_store.register_step_keys([ 'face_selector_mode', 'reference_face_position', 'reference_face_distance', 'reference_frame_number' ])
	# face mask
	group_face_mask = program.add_argument_group('face mask')
	group_face_mask.add_argument('--face-mask-types', help = wording.get('help.face_mask_types').format(choices = ', '.join(facefusion.choices.face_mask_types)), default = config.get_str_list('face_mask.face_mask_types', 'box'), choices = facefusion.choices.face_mask_types, nargs = '+', metavar = 'FACE_MASK_TYPES')
	group_face_mask.add_argument('--face-mask-blur', help = wording.get('help.face_mask_blur'), type = float, default = config.get_float_value('face_mask.face_mask_blur', '0.3'), choices = facefusion.choices.face_mask_blur_range, metavar = create_metavar(facefusion.choices.face_mask_blur_range))
	group_face_mask.add_argument('--face-mask-padding', help = wording.get('help.face_mask_padding'), type = int, default = config.get_int_list('face_mask.face_mask_padding', '0 0 0 0'), nargs = '+')
	group_face_mask.add_argument('--face-mask-regions', help = wording.get('help.face_mask_regions').format(choices = ', '.join(facefusion.choices.face_mask_regions)), default = config.get_str_list('face_mask.face_mask_regions', ' '.join(facefusion.choices.face_mask_regions)), choices = facefusion.choices.face_mask_regions, nargs = '+', metavar = 'FACE_MASK_REGIONS')
	job_store.register_step_keys([ 'face_mask_types', 'face_mask_blur', 'face_mask_padding', 'face_mask_regions' ])
	# frame extraction
	group_frame_extraction = program.add_argument_group('frame extraction')
	group_frame_extraction.add_argument('--trim-frame-start', help = wording.get('help.trim_frame_start'), type = int, default = facefusion.config.get_int_value('frame_extraction.trim_frame_start'))
	group_frame_extraction.add_argument('--trim-frame-end',	help = wording.get('help.trim_frame_end'), type = int, default = facefusion.config.get_int_value('frame_extraction.trim_frame_end'))
	group_frame_extraction.add_argument('--temp-frame-format', help = wording.get('help.temp_frame_format'), default = config.get_str_value('frame_extraction.temp_frame_format', 'png'), choices = facefusion.choices.temp_frame_formats)
	group_frame_extraction.add_argument('--keep-temp', help = wording.get('help.keep_temp'), action = 'store_true',	default = config.get_bool_value('frame_extraction.keep_temp'))
	job_store.register_step_keys([ 'trim_frame_start', 'trim_frame_end', 'temp_frame_format', 'keep_temp' ])
	# output creation
	group_output_creation = program.add_argument_group('output creation')
	group_output_creation.add_argument('--output-image-quality', help = wording.get('help.output_image_quality'), type = int, default = config.get_int_value('output_creation.output_image_quality', '80'), choices = facefusion.choices.output_image_quality_range, metavar = create_metavar(facefusion.choices.output_image_quality_range))
	group_output_creation.add_argument('--output-image-resolution', help = wording.get('help.output_image_resolution'), default = config.get_str_value('output_creation.output_image_resolution'))
	group_output_creation.add_argument('--output-audio-encoder', help = wording.get('help.output_audio_encoder'), default = config.get_str_value('output_creation.output_audio_encoder', 'aac'), choices = facefusion.choices.output_audio_encoders)
	group_output_creation.add_argument('--output-video-encoder', help = wording.get('help.output_video_encoder'), default = config.get_str_value('output_creation.output_video_encoder', 'libx264'), choices = facefusion.choices.output_video_encoders)
	group_output_creation.add_argument('--output-video-preset', help = wording.get('help.output_video_preset'), default = config.get_str_value('output_creation.output_video_preset', 'veryfast'), choices = facefusion.choices.output_video_presets)
	group_output_creation.add_argument('--output-video-quality', help = wording.get('help.output_video_quality'), type = int, default = config.get_int_value('output_creation.output_video_quality', '80'), choices = facefusion.choices.output_video_quality_range, metavar = create_metavar(facefusion.choices.output_video_quality_range))
	group_output_creation.add_argument('--output-video-resolution', help = wording.get('help.output_video_resolution'), default = config.get_str_value('output_creation.output_video_resolution'))
	group_output_creation.add_argument('--output-video-fps', help = wording.get('help.output_video_fps'), type = float, default = config.get_str_value('output_creation.output_video_fps'))
	group_output_creation.add_argument('--skip-audio', help = wording.get('help.skip_audio'), action = 'store_true', default = config.get_bool_value('output_creation.skip_audio'))
	job_store.register_step_keys([ 'output_image_quality', 'output_image_resolution', 'output_audio_encoder', 'output_video_encoder', 'output_video_preset', 'output_video_quality', 'output_video_resolution', 'output_video_fps', 'skip_audio' ])
	# frame processors
	available_frame_processors = list_directory('facefusion/processors/frame/modules')
	program = ArgumentParser(parents = [ program ], formatter_class = program.formatter_class, add_help = True)
	group_frame_processors = program.add_argument_group('frame processors')
	group_frame_processors.add_argument('--frame-processors', help = wording.get('help.frame_processors').format(choices = ', '.join(available_frame_processors)), default = config.get_str_list('frame_processors.frame_processors', 'face_swapper'), nargs = '+')
	job_store.register_step_keys([ 'frame_processors' ])
	for frame_processor in available_frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		frame_processor_module.register_args(group_frame_processors)
	# uis
	available_ui_layouts = list_directory('facefusion/uis/layouts')
	group_uis = program.add_argument_group('uis')
	group_uis.add_argument('--open-browser', help = wording.get('help.open_browser'), action = 'store_true', default = config.get_bool_value('uis.open_browser'))
	group_uis.add_argument('--ui-layouts', help = wording.get('help.ui_layouts').format(choices = ', '.join(available_ui_layouts)), default = config.get_str_list('uis.ui_layouts', 'default'), nargs = '+')
	# job manager
	group_job_manager = program.add_argument_group('job manager')
	group_job_manager.add_argument('--job-create', help = wording.get('help.job_create'), metavar = 'JOB_ID')
	group_job_manager.add_argument('--job-submit', help = wording.get('help.job_submit'), metavar = 'JOB_ID')
	group_job_manager.add_argument('--job-submit-all', help = wording.get('help.job_submit_all'), action = 'store_true')
	group_job_manager.add_argument('--job-delete', help = wording.get('help.job_delete'), metavar = 'JOB_ID')
	group_job_manager.add_argument('--job-delete-all', help = wording.get('help.job_delete_all'), action = 'store_true')
	group_job_manager.add_argument('--job-add-step', help = wording.get('help.job_add_step'), metavar = 'JOB_ID')
	group_job_manager.add_argument('--job-remix-step', help = wording.get('help.job_remix_step'), nargs = 2, metavar = ('JOB_ID', 'STEP_INDEX'))
	group_job_manager.add_argument('--job-insert-step', help = wording.get('help.job_insert_step'), nargs = 2, metavar = ('JOB_ID', 'STEP_INDEX'))
	group_job_manager.add_argument('--job-remove-step', help = wording.get('help.job_remove_step'), nargs = 2, metavar = ('JOB_ID', 'STEP_INDEX'))
	# job runner
	group_job_runner = program.add_argument_group('job runner')
	group_job_runner.add_argument('--job-run', help = wording.get('help.job_run'), metavar = 'JOB_ID')
	group_job_runner.add_argument('--job-run-all', help = wording.get('help.job_run_all'), action = 'store_true')
	group_job_runner.add_argument('--job-retry', help = wording.get('help.job_retry'), metavar = 'JOB_ID')
	group_job_runner.add_argument('--job-retry-all', help = wording.get('help.job_retry_all'), action = 'store_true')
	return program


def apply_config_path(program : ArgumentParser) -> None:
	known_args, _ = program.parse_known_args()
	facefusion.globals.config_path = known_args.config_path


def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	# general
	facefusion.globals.source_paths = args.source_paths
	facefusion.globals.target_path = args.target_path
	facefusion.globals.output_path = args.output_path
	facefusion.globals.jobs_path = args.jobs_path
	# misc
	facefusion.globals.force_download = args.force_download
	facefusion.globals.skip_download = args.skip_download
	facefusion.globals.headless = args.headless
	facefusion.globals.log_level = args.log_level
	# execution
	facefusion.globals.execution_device_id = args.execution_device_id
	facefusion.globals.execution_providers = args.execution_providers
	facefusion.globals.execution_thread_count = args.execution_thread_count
	facefusion.globals.execution_queue_count = args.execution_queue_count
	# memory
	facefusion.globals.video_memory_strategy = args.video_memory_strategy
	facefusion.globals.system_memory_limit = args.system_memory_limit
	# face analyser
	facefusion.globals.face_analyser_order = args.face_analyser_order
	facefusion.globals.face_analyser_age = args.face_analyser_age
	facefusion.globals.face_analyser_gender = args.face_analyser_gender
	facefusion.globals.face_detector_model = args.face_detector_model
	facefusion.globals.face_detector_size = args.face_detector_size
	facefusion.globals.face_detector_score = args.face_detector_score
	facefusion.globals.face_landmarker_score = args.face_landmarker_score
	# face selector
	facefusion.globals.face_selector_mode = args.face_selector_mode
	facefusion.globals.reference_face_position = args.reference_face_position
	facefusion.globals.reference_face_distance = args.reference_face_distance
	facefusion.globals.reference_frame_number = args.reference_frame_number
	# face mask
	facefusion.globals.face_mask_types = args.face_mask_types
	facefusion.globals.face_mask_blur = args.face_mask_blur
	facefusion.globals.face_mask_padding = normalize_padding(args.face_mask_padding)
	facefusion.globals.face_mask_regions = args.face_mask_regions
	# frame extraction
	facefusion.globals.trim_frame_start = args.trim_frame_start
	facefusion.globals.trim_frame_end = args.trim_frame_end
	facefusion.globals.temp_frame_format = args.temp_frame_format
	facefusion.globals.keep_temp = args.keep_temp
	# output creation
	facefusion.globals.output_image_quality = args.output_image_quality
	if is_image(args.target_path):
		output_image_resolution = detect_image_resolution(args.target_path)
		output_image_resolutions = create_image_resolutions(output_image_resolution)
		if args.output_image_resolution in output_image_resolutions:
			facefusion.globals.output_image_resolution = args.output_image_resolution
		else:
			facefusion.globals.output_image_resolution = pack_resolution(output_image_resolution)
	facefusion.globals.output_audio_encoder = args.output_audio_encoder
	facefusion.globals.output_video_encoder = args.output_video_encoder
	facefusion.globals.output_video_preset = args.output_video_preset
	facefusion.globals.output_video_quality = args.output_video_quality
	if is_video(args.target_path):
		output_video_resolution = detect_video_resolution(args.target_path)
		output_video_resolutions = create_video_resolutions(output_video_resolution)
		if args.output_video_resolution in output_video_resolutions:
			facefusion.globals.output_video_resolution = args.output_video_resolution
		else:
			facefusion.globals.output_video_resolution = pack_resolution(output_video_resolution)
	if args.output_video_fps or is_video(args.target_path):
		facefusion.globals.output_video_fps = normalize_fps(args.output_video_fps) or detect_video_fps(args.target_path)
	facefusion.globals.skip_audio = args.skip_audio
	# frame processors
	available_frame_processors = list_directory('facefusion/processors/frame/modules')
	facefusion.globals.frame_processors = args.frame_processors
	for frame_processor in available_frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		frame_processor_module.apply_args(program)
	# uis
	facefusion.globals.open_browser = args.open_browser
	facefusion.globals.ui_layouts = args.ui_layouts


def run(program : ArgumentParser) -> None:
	args = program.parse_args()

	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	if args.job_create or args.job_submit or args.job_submit_all or args.job_delete or args.job_delete_all or args.job_add_step or args.job_remix_step or args.job_insert_step or args.job_remove_step:
		if not job_manager.init_jobs(facefusion.globals.jobs_path):
			hard_exit(1)
		error_code = route_job_manager(program)
		hard_exit(error_code)
	if facefusion.globals.force_download:
		force_download()
		return conditional_exit(0)
	if not pre_check() or not content_analyser.pre_check() or not face_analyser.pre_check() or not face_masker.pre_check() or not voice_extractor.pre_check():
		return conditional_exit(2)
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		if not frame_processor_module.pre_check():
			return conditional_exit(2)
	if args.job_run or args.job_run_all or args.job_retry or args.job_retry_all:
		if not job_manager.init_jobs(facefusion.globals.jobs_path):
			hard_exit(1)
		error_code = route_job_runner(program)
		hard_exit(error_code)
	elif facefusion.globals.headless:
		if not job_manager.init_jobs(facefusion.globals.jobs_path):
			hard_exit(1)
		error_core = process_headless(program)
		hard_exit(error_core)
	else:
		import facefusion.uis.core as ui

		for ui_layout in ui.get_ui_layouts_modules(facefusion.globals.ui_layouts):
			if not ui_layout.pre_check():
				return conditional_exit(2)
		ui.launch()


def pre_check() -> bool:
	if sys.version_info < (3, 9):
		logger.error(wording.get('python_not_supported').format(version = '3.9'), __name__.upper())
		return False
	if not shutil.which('ffmpeg'):
		logger.error(wording.get('ffmpeg_not_installed'), __name__.upper())
		return False
	return True


def conditional_process() -> ErrorCode:
	start_time = time()
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		while not frame_processor_module.post_check():
			logger.disable()
			sleep(0.5)
		logger.enable()
		if not frame_processor_module.pre_process('output'):
			return 2
	conditional_append_reference_faces()
	if is_image(facefusion.globals.target_path):
		return process_image(start_time)
	if is_video(facefusion.globals.target_path):
		return process_video(start_time)
	return 0


def conditional_append_reference_faces() -> None:
	if 'reference' in facefusion.globals.face_selector_mode and not get_reference_faces():
		source_frames = read_static_images(facefusion.globals.source_paths)
		source_face = get_average_face(source_frames)
		if is_video(facefusion.globals.target_path):
			reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		else:
			reference_frame = read_image(facefusion.globals.target_path)
		reference_face = get_one_face(reference_frame, facefusion.globals.reference_face_position)
		append_reference_face('origin', reference_face)
		if source_face and reference_face:
			for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
				abstract_reference_frame = frame_processor_module.get_reference_frame(source_face, reference_face, reference_frame)
				if numpy.any(abstract_reference_frame):
					reference_frame = abstract_reference_frame
					reference_face = get_one_face(reference_frame, facefusion.globals.reference_face_position)
					append_reference_face(frame_processor_module.__name__, reference_face)


def force_download() -> None:
	download_directory_path = resolve_relative_path('../.assets/models')
	available_frame_processors = list_directory('facefusion/processors/frame/modules')
	models =\
	[
		content_analyser.MODELS,
		face_analyser.MODELS,
		face_masker.MODELS,
		voice_extractor.MODELS
	]

	for frame_processor_module in get_frame_processors_modules(available_frame_processors):
		if hasattr(frame_processor_module, 'MODELS'):
			models.append(frame_processor_module.MODELS)
	model_urls = [ models[model].get('url') for models in models for model in models ]
	conditional_download(download_directory_path, model_urls)


def route_job_manager(program : ArgumentParser) -> ErrorCode:
	args = program.parse_args()
	step_program = reduce_args(program, job_store.get_step_keys())
	step_args = vars(step_program.parse_args())

	if args.job_create:
		if job_manager.create_job(args.job_create):
			logger.info(wording.get('job_created').format(job_id = args.job_create), __name__.upper())
			return 0
		logger.error(wording.get('job_not_created').format(job_id = args.job_create), __name__.upper())
		return 1
	if args.job_submit:
		if job_manager.submit_job(args.job_submit):
			logger.info(wording.get('job_submitted').format(job_id = args.job_submit), __name__.upper())
			return 0
		logger.error(wording.get('job_not_submitted').format(job_id = args.job_submit), __name__.upper())
		return 1
	if args.job_submit_all:
		if job_manager.submit_jobs():
			logger.info(wording.get('job_all_submitted'), __name__.upper())
			return 0
		logger.error(wording.get('job_all_not_submitted'), __name__.upper())
		return 1
	if args.job_delete:
		if job_manager.delete_job(args.job_delete):
			logger.info(wording.get('job_deleted').format(job_id = args.job_delete), __name__.upper())
			return 0
		logger.error(wording.get('job_not_deleted').format(job_id = args.job_delete), __name__.upper())
		return 1
	if args.job_delete_all:
		if job_manager.delete_jobs():
			logger.info(wording.get('job_all_deleted'), __name__.upper())
			return 0
		logger.error(wording.get('job_all_not_deleted'), __name__.upper())
		return 1
	if args.job_add_step:
		if job_manager.add_step(args.job_add_step, step_args):
			logger.info(wording.get('job_step_added').format(job_id = args.job_add_step), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_added').format(job_id = args.job_add_step), __name__.upper())
		return 1
	if args.job_remix_step:
		job_id, step_index = args.job_remix_step
		step_index = int(step_index)

		if job_manager.remix_step(job_id, step_index, step_args):
			logger.info(wording.get('job_remix_step_added').format(job_id = job_id, step_index = step_index), __name__.upper())
			return 0
		logger.error(wording.get('job_remix_step_not_added').format(job_id = job_id, step_index = step_index), __name__.upper())
		return 1
	if args.job_insert_step:
		job_id, step_index = args.job_insert_step
		step_index = int(step_index)

		if job_manager.insert_step(job_id, step_index, step_args):
			logger.info(wording.get('job_step_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
		return 1
	if args.job_remove_step:
		job_id, step_index = args.job_remove_step
		step_index = int(step_index)

		if job_manager.remove_step(job_id, step_index):
			logger.info(wording.get('job_step_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
		return 1
	return 1


def route_job_runner(program : ArgumentParser) -> ErrorCode:
	args = program.parse_args()

	if args.job_run:
		logger.info(wording.get('running_job').format(job_id = args.job_run), __name__.upper())
		if job_runner.run_job(args.job_run, process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = args.job_run), __name__.upper())
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = args.job_run), __name__.upper())
		return 1
	if args.job_run_all:
		logger.info(wording.get('running_jobs'), __name__.upper())
		if job_runner.run_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__.upper())
		return 1
	if args.job_retry:
		logger.info(wording.get('retrying_job').format(job_id = args.job_retry), __name__.upper())
		if job_runner.retry_job(args.job_retry, process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = args.job_retry), __name__.upper())
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = args.job_retry), __name__.upper())
		return 1
	if args.job_retry_all:
		logger.info(wording.get('retrying_jobs'), __name__.upper())
		if job_runner.retry_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__.upper())
		return 1
	return 2


def process_step(step_args : Args) -> bool:
	program = create_program()
	program = update_args(program, step_args)
	program = import_globals(program, job_store.get_job_keys(), [ facefusion, facefusion.processors.frame ])

	if validate_args(program):
		apply_args(program)
		clear_frame_processors_modules()
		error_code = conditional_process()
		return error_code == 0
	return False


def process_headless(program : ArgumentParser) -> ErrorCode:
	job_id = job_helper.suggest_job_id('headless')
	step_program = reduce_args(program, job_store.get_step_keys())
	step_args = vars(step_program.parse_args())

	if job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
		return 0
	return 1


def process_image(start_time : float) -> ErrorCode:
	if analyse_image(facefusion.globals.target_path):
		return 3
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(facefusion.globals.target_path)
	# create temp
	logger.debug(wording.get('creating_temp'), __name__.upper())
	create_temp_directory(facefusion.globals.target_path)
	# copy image
	process_manager.start()
	temp_image_resolution = pack_resolution(restrict_image_resolution(facefusion.globals.target_path, unpack_resolution(facefusion.globals.output_image_resolution)))
	logger.info(wording.get('copying_image').format(resolution = temp_image_resolution), __name__.upper())
	if copy_image(facefusion.globals.target_path, temp_image_resolution):
		logger.debug(wording.get('copying_image_succeed'), __name__.upper())
	else:
		logger.error(wording.get('copying_image_failed'), __name__.upper())
		return 1
	# process image
	temp_file_path = get_temp_file_path(facefusion.globals.target_path)
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		logger.info(wording.get('processing'), frame_processor_module.NAME)
		frame_processor_module.process_image(facefusion.globals.source_paths, temp_file_path, temp_file_path)
		frame_processor_module.post_process()
	if is_process_stopping():
		return 4
	# finalize image
	logger.info(wording.get('finalizing_image').format(resolution = facefusion.globals.output_image_resolution), __name__.upper())
	if finalize_image(facefusion.globals.target_path, facefusion.globals.output_path, facefusion.globals.output_image_resolution):
		logger.debug(wording.get('finalizing_image_succeed'), __name__.upper())
	else:
		logger.warn(wording.get('finalizing_image_skipped'), __name__.upper())
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(facefusion.globals.target_path)
	# validate image
	if is_image(facefusion.globals.output_path):
		seconds = '{:.2f}'.format((time() - start_time) % 60)
		logger.info(wording.get('processing_image_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_image_failed'), __name__.upper())
		return 1
	process_manager.end()
	return 0


def process_video(start_time : float) -> ErrorCode:
	if analyse_video(facefusion.globals.target_path, facefusion.globals.trim_frame_start, facefusion.globals.trim_frame_end):
		return 3
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(facefusion.globals.target_path)
	# create temp
	logger.debug(wording.get('creating_temp'), __name__.upper())
	create_temp_directory(facefusion.globals.target_path)
	# extract frames
	process_manager.start()
	temp_video_resolution = pack_resolution(restrict_video_resolution(facefusion.globals.target_path, unpack_resolution(facefusion.globals.output_video_resolution)))
	temp_video_fps = restrict_video_fps(facefusion.globals.target_path, facefusion.globals.output_video_fps)
	logger.info(wording.get('extracting_frames').format(resolution = temp_video_resolution, fps = temp_video_fps), __name__.upper())
	if extract_frames(facefusion.globals.target_path, temp_video_resolution, temp_video_fps):
		logger.debug(wording.get('extracting_frames_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			return 4
		logger.error(wording.get('extracting_frames_failed'), __name__.upper())
		return 1
	# process frames
	temp_frame_paths = get_temp_frame_paths(facefusion.globals.target_path)
	if temp_frame_paths:
		for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
			logger.info(wording.get('processing'), frame_processor_module.NAME)
			frame_processor_module.process_video(facefusion.globals.source_paths, temp_frame_paths)
			frame_processor_module.post_process()
		if is_process_stopping():
			return 4
	else:
		logger.error(wording.get('temp_frames_not_found'), __name__.upper())
		return 1
	# merge video
	logger.info(wording.get('merging_video').format(resolution = facefusion.globals.output_video_resolution, fps = facefusion.globals.output_video_fps), __name__.upper())
	if merge_video(facefusion.globals.target_path, facefusion.globals.output_video_resolution, facefusion.globals.output_video_fps):
		logger.debug(wording.get('merging_video_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			return 4
		logger.error(wording.get('merging_video_failed'), __name__.upper())
		return 1
	# handle audio
	if facefusion.globals.skip_audio:
		logger.info(wording.get('skipping_audio'), __name__.upper())
		move_temp_file(facefusion.globals.target_path, facefusion.globals.output_path)
	else:
		if 'lip_syncer' in facefusion.globals.frame_processors:
			source_audio_path = get_first(filter_audio_paths(facefusion.globals.source_paths))
			if source_audio_path and replace_audio(facefusion.globals.target_path, source_audio_path, facefusion.globals.output_path):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					return 4
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp_file(facefusion.globals.target_path, facefusion.globals.output_path)
		else:
			if restore_audio(facefusion.globals.target_path, facefusion.globals.output_path, facefusion.globals.output_video_fps):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					return 4
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp_file(facefusion.globals.target_path, facefusion.globals.output_path)
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(facefusion.globals.target_path)
	# validate video
	if is_video(facefusion.globals.output_path):
		seconds = '{:.2f}'.format((time() - start_time))
		logger.info(wording.get('processing_video_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_video_failed'), __name__.upper())
		return 1
	process_manager.end()
	return 0


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__.upper())
	return process_manager.is_pending()
