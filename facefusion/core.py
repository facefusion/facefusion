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
from facefusion.face_analyser import get_one_face, get_average_face
from facefusion.face_store import get_reference_faces, append_reference_face
from facefusion import face_analyser, face_masker, content_analyser, config, process_manager, metadata, logger, wording, voice_extractor, config_mapping
from facefusion.content_analyser import analyse_image, analyse_video
from facefusion.processors.frame.core import get_frame_processors_modules, load_frame_processor_module
from facefusion.common_helper import create_metavar, get_first
from facefusion.execution import encode_execution_providers, decode_execution_providers
from facefusion.normalizer import normalize_output_path, normalize_padding, normalize_fps
from facefusion.memory import limit_system_memory
from facefusion.statistics import conditional_log_statistics
from facefusion.download import conditional_download
from facefusion.filesystem import list_directory, get_temp_frame_paths, create_temp, move_temp, clear_temp, is_image, is_video, is_file, filter_audio_paths, resolve_relative_path
from facefusion.ffmpeg import extract_frames, merge_video, copy_image, finalize_image, restore_audio, replace_audio
from facefusion.vision import read_image, read_static_images, detect_image_resolution, restrict_video_fps, create_image_resolutions, get_video_frame, detect_video_resolution, detect_video_fps, restrict_video_resolution, restrict_image_resolution, create_video_resolutions, pack_resolution, unpack_resolution

onnxruntime.set_default_logger_severity(3)
warnings.filterwarnings('ignore', category = UserWarning, module = 'gradio')


def cli() -> None:
	signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
	program = ArgumentParser(formatter_class = lambda prog: HelpFormatter(prog, max_help_position = 160), add_help = False)
    # general
	program.add_argument('-c', '--config_path', help = wording.get('help.config_path'), dest = 'config_path')
	program.add_argument('-s', '--source', help = wording.get('help.source'), action = 'append', dest = 'source_paths')
	program.add_argument('-t', '--target', help = wording.get('help.target'), dest = 'target_path')
	program.add_argument('-o', '--output', help = wording.get('help.output'), dest = 'output_path')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	# misc
	group_misc = program.add_argument_group('misc')
	group_misc.add_argument('--force-download', help = wording.get('help.force_download'), action = 'store_true')
	group_misc.add_argument('--skip-download', help = wording.get('help.skip_download'), action = 'store_true')
	group_misc.add_argument('--headless', help = wording.get('help.headless'), action = 'store_true')
	group_misc.add_argument('--log-level', help = wording.get('help.log_level'))
	# execution
	execution_providers = encode_execution_providers(onnxruntime.get_available_providers())
	group_execution = program.add_argument_group('execution')
	group_execution.add_argument('--execution-providers', help = wording.get('help.execution_providers').format(choices = ', '.join(execution_providers)), choices = execution_providers, nargs = '+', metavar = 'EXECUTION_PROVIDERS')
	group_execution.add_argument('--execution-thread-count', help = wording.get('help.execution_thread_count'), type = int, choices = facefusion.choices.execution_thread_count_range, metavar = create_metavar(facefusion.choices.execution_thread_count_range))
	group_execution.add_argument('--execution-queue-count', help = wording.get('help.execution_queue_count'), type = int, choices = facefusion.choices.execution_queue_count_range, metavar = create_metavar(facefusion.choices.execution_queue_count_range))
	# memory
	group_memory = program.add_argument_group('memory')
	group_memory.add_argument('--video-memory-strategy', help = wording.get('help.video_memory_strategy'), choices = facefusion.choices.video_memory_strategies)
	group_memory.add_argument('--system-memory-limit', help = wording.get('help.system_memory_limit'), type = int, choices = facefusion.choices.system_memory_limit_range, metavar = create_metavar(facefusion.choices.system_memory_limit_range))
	# face analyser
	group_face_analyser = program.add_argument_group('face analyser')
	group_face_analyser.add_argument('--face-analyser-order', help = wording.get('help.face_analyser_order'), choices = facefusion.choices.face_analyser_orders)
	group_face_analyser.add_argument('--face-analyser-age', help = wording.get('help.face_analyser_age'), choices = facefusion.choices.face_analyser_ages)
	group_face_analyser.add_argument('--face-analyser-gender', help = wording.get('help.face_analyser_gender'), choices = facefusion.choices.face_analyser_genders)
	group_face_analyser.add_argument('--face-detector-model', help = wording.get('help.face_detector_model'), choices = facefusion.choices.face_detector_set.keys())
	group_face_analyser.add_argument('--face-detector-size', help = wording.get('help.face_detector_size'))
	group_face_analyser.add_argument('--face-detector-score', help = wording.get('help.face_detector_score'), type = float, choices = facefusion.choices.face_detector_score_range, metavar = create_metavar(facefusion.choices.face_detector_score_range))
	group_face_analyser.add_argument('--face-landmarker-score', help = wording.get('help.face_landmarker_score'), type = float, choices = facefusion.choices.face_landmarker_score_range, metavar = create_metavar(facefusion.choices.face_landmarker_score_range))
	# face selector
	group_face_selector = program.add_argument_group('face selector')
	group_face_selector.add_argument('--face-selector-mode', help = wording.get('help.face_selector_mode'), choices = facefusion.choices.face_selector_modes)
	group_face_selector.add_argument('--reference-face-position', help = wording.get('help.reference_face_position'), type = int)
	group_face_selector.add_argument('--reference-face-distance', help = wording.get('help.reference_face_distance'), type = float, choices = facefusion.choices.reference_face_distance_range, metavar = create_metavar(facefusion.choices.reference_face_distance_range))
	group_face_selector.add_argument('--reference-frame-number', help = wording.get('help.reference_frame_number'), type = int)
	# face mask
	group_face_mask = program.add_argument_group('face mask')
	group_face_mask.add_argument('--face-mask-types', help = wording.get('help.face_mask_types').format(choices = ', '.join(facefusion.choices.face_mask_types)), choices = facefusion.choices.face_mask_types, nargs = '+', metavar = 'FACE_MASK_TYPES')
	group_face_mask.add_argument('--face-mask-blur', help = wording.get('help.face_mask_blur'), type = float, choices = facefusion.choices.face_mask_blur_range, metavar = create_metavar(facefusion.choices.face_mask_blur_range))
	group_face_mask.add_argument('--face-mask-padding', help = wording.get('help.face_mask_padding'), type = int)
	group_face_mask.add_argument('--face-mask-regions', help = wording.get('help.face_mask_regions').format(choices = ', '.join(facefusion.choices.face_mask_regions)), choices = facefusion.choices.face_mask_regions, nargs = '+', metavar = 'FACE_MASK_REGIONS')
	# frame extraction
	group_frame_extraction = program.add_argument_group('frame extraction')
	group_frame_extraction.add_argument('--trim-frame-start', help = wording.get('help.trim_frame_start'), type = int)
	group_frame_extraction.add_argument('--trim-frame-end',	help = wording.get('help.trim_frame_end'), type = int)
	group_frame_extraction.add_argument('--temp-frame-format', help = wording.get('help.temp_frame_format'), choices = facefusion.choices.temp_frame_formats)
	group_frame_extraction.add_argument('--keep-temp', help = wording.get('help.keep_temp'), action = 'store_true',	default = config.get_bool_value('frame_extraction.keep_temp'))
	# output creation
	group_output_creation = program.add_argument_group('output creation')
	group_output_creation.add_argument('--output-image-quality', help = wording.get('help.output_image_quality'), type = int, choices = facefusion.choices.output_image_quality_range, metavar = create_metavar(facefusion.choices.output_image_quality_range))
	group_output_creation.add_argument('--output-image-resolution', help = wording.get('help.output_image_resolution')) 
	group_output_creation.add_argument('--output-video-encoder', help = wording.get('help.output_video_encoder'), choices = facefusion.choices.output_video_encoders)
	group_output_creation.add_argument('--output-video-preset', help = wording.get('help.output_video_preset'), choices = facefusion.choices.output_video_presets)
	group_output_creation.add_argument('--output-video-quality', help = wording.get('help.output_video_quality'), type = int, choices = facefusion.choices.output_video_quality_range, metavar = create_metavar(facefusion.choices.output_video_quality_range))
	group_output_creation.add_argument('--output-video-resolution', help = wording.get('help.output_video_resolution'))
	group_output_creation.add_argument('--output-video-fps', help = wording.get('help.output_video_fps'), type = float)
	group_output_creation.add_argument('--skip-audio', help = wording.get('help.skip_audio'), action = 'store_true')
	# frame processors
	available_frame_processors = list_directory('facefusion/processors/frame/modules')
	program = ArgumentParser(parents = [ program ], formatter_class = program.formatter_class, add_help = True)
	group_frame_processors = program.add_argument_group('frame processors')
	group_frame_processors.add_argument('--frame-processors', help = wording.get('help.frame_processors').format(choices = ', '.join(available_frame_processors)), nargs = '+')
	for frame_processor in available_frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		frame_processor_module.register_args(group_frame_processors)
	# uis
	available_ui_layouts = list_directory('facefusion/uis/layouts')
	group_uis = program.add_argument_group('uis')
	group_uis.add_argument('--ui-layouts', help = wording.get('help.ui_layouts').format(choices = ', '.join(available_ui_layouts)), nargs = '+')
	run(program)


def validate_args(program : ArgumentParser) -> None:
	try:
		for action in program._actions:
			if action.default:
				if isinstance(action.default, list):
					for default in action.default:
						program._check_value(action, default)
				else:
					program._check_value(action, action.default)
	except Exception as exception:
		program.error(str(exception))


def apply_config(program : ArgumentParser) -> None:
	args = program.parse_args()
	facefusion.globals.config_path = args.config_path	
	if not is_file(args.config_path) and args.config_path is not None:
		logger.error(wording.get('select_config_file'), __name__.upper())
		logger.error(wording.get('using_default_config'), __name__.upper())
		facefusion.globals.config_path = 'facefusion.ini'
	config.CONFIG = None
	for attribute, (config_function, config_path, default_value) in config_mapping.attribute_config_mapping.items():
		if default_value is not None:
			setattr(facefusion.globals, attribute, config_function(config_path, default_value))
		else:
			setattr(facefusion.globals, attribute, config_function(config_path))
		if attribute == 'execution_providers':
			setattr(facefusion.globals, attribute, decode_execution_providers(getattr(facefusion.globals, attribute)))
		elif attribute == 'face_mask_padding':
			setattr(facefusion.globals, attribute, normalize_padding(getattr(facefusion.globals, attribute)))
		elif attribute == 'frame_processors':
				available_frame_processors = list_directory('facefusion/processors/frame/modules')
				setattr(facefusion.globals, attribute, config_function(config_path, default_value))
				for frame_processor in available_frame_processors:
					frame_processor_module = load_frame_processor_module(frame_processor)
					frame_processor_module.apply_args(program)
	if is_image(facefusion.globals.target_path):
					output_image_resolution = detect_image_resolution(facefusion.globals.target_path)
					output_image_resolutions = create_image_resolutions(output_image_resolution)
					if facefusion.globals.output_image_resolution in output_image_resolutions:
						facefusion.globals.output_image_resolution
					else:
						facefusion.globals.output_image_resolution = pack_resolution(output_image_resolution)
	if is_video(facefusion.globals.target_path):
			facefusion.globals.output_video_fps = normalize_fps(facefusion.globals.output_video_fps) or detect_video_fps(facefusion.globals.target_path)
			output_video_resolution = detect_video_resolution(facefusion.globals.target_path)
			output_video_resolutions = create_video_resolutions(output_video_resolution)
			if facefusion.globals.output_video_resolution in output_video_resolutions:
				facefusion.globals.output_video_resolution
			else:
				facefusion.globals.output_video_resolution = pack_resolution(output_video_resolution)
		
	
def apply_args(program : ArgumentParser) -> None:
	args = program.parse_args()
	if is_image(args.target_path):
					output_image_resolution = detect_image_resolution(args.target_path)
					output_image_resolutions = create_image_resolutions(output_image_resolution)
					if args.output_image_resolution in output_image_resolutions:
						facefusion.globals.output_image_resolution = args.output_image_resolution
					else:
						facefusion.globals.output_image_resolution = pack_resolution(output_image_resolution)
	if is_video(args.target_path):
			facefusion.globals.output_video_fps = normalize_fps(args.output_video_fps) or detect_video_fps(args.target_path)
			output_video_resolution = detect_video_resolution(args.target_path)
			output_video_resolutions = create_video_resolutions(output_video_resolution)
			if args.output_video_resolution in output_video_resolutions:
				facefusion.globals.output_video_resolution = args.output_video_resolution
			else:
				facefusion.globals.output_video_resolution = pack_resolution(output_video_resolution)
	for attribute, (config_function, config_path,default_value) in config_mapping.attribute_config_mapping.items(): 
		if hasattr(args, attribute) and getattr(args, attribute) is not None:
			if attribute == 'face_detector_model':
				setattr(facefusion.globals, attribute, getattr(args, attribute))
				if args.face_detector_size in facefusion.choices.face_detector_set[args.face_detector_model]:
					facefusion.globals.face_detector_size = args.face_detector_size
			elif attribute == 'execution_providers':
				setattr(facefusion.globals, attribute, decode_execution_providers(getattr(args, attribute)))
			elif attribute == 'face_mask_padding':
				setattr(facefusion.globals, attribute, normalize_padding(getattr(args, attribute)))		
			elif attribute == 'output_video_fps':
				if args.output_video_fps:
					facefusion.globals.output_video_fps = normalize_fps(args.output_video_fps)
				elif is_video(args.target_path):
					facefusion.globals.output_video_fps = detect_video_fps(args.target_path)
			elif attribute == 'frame_processors':
				available_frame_processors = list_directory('facefusion/processors/frame/modules')
				setattr(facefusion.globals, attribute, getattr(args, attribute))
				for frame_processor in available_frame_processors:
					frame_processor_module = load_frame_processor_module(frame_processor)
					frame_processor_module.apply_args(program)
			else:
				setattr(facefusion.globals, attribute, getattr(args, attribute))


def run(program : ArgumentParser) -> None:
	validate_args(program)
	apply_config(program)
	apply_args(program)
	
	logger.init(facefusion.globals.log_level)

	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	if facefusion.globals.force_download:
		force_download()
		return
	if not pre_check() or not content_analyser.pre_check() or not face_analyser.pre_check() or not face_masker.pre_check() or not voice_extractor.pre_check():
		return
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		if not frame_processor_module.pre_check():
			return
	if facefusion.globals.headless:
		conditional_process()
	else:
		import facefusion.uis.core as ui

		for ui_layout in ui.get_ui_layouts_modules(facefusion.globals.ui_layouts):
			if not ui_layout.pre_check():
				return
		ui.launch()


def destroy() -> None:
	process_manager.stop()
	while process_manager.is_processing():
		sleep(0.5)
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	sys.exit(0)


def pre_check() -> bool:
	if sys.version_info < (3, 9):
		logger.error(wording.get('python_not_supported').format(version = '3.9'), __name__.upper())
		return False
	if not shutil.which('ffmpeg'):
		logger.error(wording.get('ffmpeg_not_installed'), __name__.upper())
		return False
	return True


def conditional_process() -> None:
	start_time = time()
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		while not frame_processor_module.post_check():
			logger.disable()
			sleep(0.5)
		logger.enable()
		if not frame_processor_module.pre_process('output'):
			return
	conditional_append_reference_faces()
	if is_image(facefusion.globals.target_path):
		process_image(start_time)
	if is_video(facefusion.globals.target_path):
		process_video(start_time)


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
	model_list =\
	[
		content_analyser.MODELS,
		face_analyser.MODELS,
		face_masker.MODELS,
		voice_extractor.MODELS
	]

	for frame_processor_module in get_frame_processors_modules(available_frame_processors):
		if hasattr(frame_processor_module, 'MODELS'):
			model_list.append(frame_processor_module.MODELS)
	model_urls = [ models[model].get('url') for models in model_list for model in models ]
	conditional_download(download_directory_path, model_urls)


def process_image(start_time : float) -> None:
	normed_output_path = normalize_output_path(facefusion.globals.target_path, facefusion.globals.output_path)
	if analyse_image(facefusion.globals.target_path):
		return
	# copy image
	process_manager.start()
	temp_image_resolution = pack_resolution(restrict_image_resolution(facefusion.globals.target_path, unpack_resolution(facefusion.globals.output_image_resolution)))
	logger.info(wording.get('copying_image').format(resolution = temp_image_resolution), __name__.upper())
	if copy_image(facefusion.globals.target_path, normed_output_path, temp_image_resolution):
		logger.debug(wording.get('copying_image_succeed'), __name__.upper())
	else:
		logger.error(wording.get('copying_image_failed'), __name__.upper())
		return
	# process image
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		logger.info(wording.get('processing'), frame_processor_module.NAME)
		frame_processor_module.process_image(facefusion.globals.source_paths, normed_output_path, normed_output_path)
		frame_processor_module.post_process()
	if is_process_stopping():
		return
	# finalize image
	logger.info(wording.get('finalizing_image').format(resolution = facefusion.globals.output_image_resolution), __name__.upper())
	if finalize_image(normed_output_path, facefusion.globals.output_image_resolution):
		logger.debug(wording.get('finalizing_image_succeed'), __name__.upper())
	else:
		logger.warn(wording.get('finalizing_image_skipped'), __name__.upper())
	# validate image
	if is_image(normed_output_path):
		seconds = '{:.2f}'.format((time() - start_time) % 60)
		logger.info(wording.get('processing_image_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_image_failed'), __name__.upper())
	process_manager.end()


def process_video(start_time : float) -> None:
	normed_output_path = normalize_output_path(facefusion.globals.target_path, facefusion.globals.output_path)
	if analyse_video(facefusion.globals.target_path, facefusion.globals.trim_frame_start, facefusion.globals.trim_frame_end):
		return
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp(facefusion.globals.target_path)
	# create temp
	logger.debug(wording.get('creating_temp'), __name__.upper())
	create_temp(facefusion.globals.target_path)
	# extract frames
	process_manager.start()
	temp_video_resolution = pack_resolution(restrict_video_resolution(facefusion.globals.target_path, unpack_resolution(facefusion.globals.output_video_resolution)))
	temp_video_fps = restrict_video_fps(facefusion.globals.target_path, facefusion.globals.output_video_fps)
	logger.info(wording.get('extracting_frames').format(resolution = temp_video_resolution, fps = temp_video_fps), __name__.upper())
	if extract_frames(facefusion.globals.target_path, temp_video_resolution, temp_video_fps):
		logger.debug(wording.get('extracting_frames_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			return
		logger.error(wording.get('extracting_frames_failed'), __name__.upper())
		return
	# process frames
	temp_frame_paths = get_temp_frame_paths(facefusion.globals.target_path)
	if temp_frame_paths:
		for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
			logger.info(wording.get('processing'), frame_processor_module.NAME)
			frame_processor_module.process_video(facefusion.globals.source_paths, temp_frame_paths)
			frame_processor_module.post_process()
		if is_process_stopping():
			return
	else:
		logger.error(wording.get('temp_frames_not_found'), __name__.upper())
		return
	# merge video
	logger.info(wording.get('merging_video').format(resolution = facefusion.globals.output_video_resolution, fps = facefusion.globals.output_video_fps), __name__.upper())
	if merge_video(facefusion.globals.target_path, facefusion.globals.output_video_resolution, facefusion.globals.output_video_fps):
		logger.debug(wording.get('merging_video_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			return
		logger.error(wording.get('merging_video_failed'), __name__.upper())
		return
	# handle audio
	if facefusion.globals.skip_audio:
		logger.info(wording.get('skipping_audio'), __name__.upper())
		move_temp(facefusion.globals.target_path, normed_output_path)
	else:
		if 'lip_syncer' in facefusion.globals.frame_processors:
			source_audio_path = get_first(filter_audio_paths(facefusion.globals.source_paths))
			if source_audio_path and replace_audio(facefusion.globals.target_path, source_audio_path, normed_output_path):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					return
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp(facefusion.globals.target_path, normed_output_path)
		else:
			if restore_audio(facefusion.globals.target_path, normed_output_path, facefusion.globals.output_video_fps):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					return
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp(facefusion.globals.target_path, normed_output_path)
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp(facefusion.globals.target_path)
	# validate video
	if is_video(normed_output_path):
		seconds = '{:.2f}'.format((time() - start_time))
		logger.info(wording.get('processing_video_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_video_failed'), __name__.upper())
	process_manager.end()


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__.upper())
	return process_manager.is_pending()
