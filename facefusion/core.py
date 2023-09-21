#!/usr/bin/env python3

import os
# single thread doubles cuda performance
os.environ['OMP_NUM_THREADS'] = '1'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
import warnings
from typing import List
import platform
import signal
import shutil
import argparse
import onnxruntime
import tensorflow

import facefusion.choices
import facefusion.globals
from facefusion import wording, metadata
from facefusion.predictor import predict_image, predict_video
from facefusion.processors.frame.core import get_frame_processors_modules
from facefusion.utilities import is_image, is_video, detect_fps, compress_image, merge_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clear_temp, normalize_output_path, list_module_names, decode_execution_providers, encode_execution_providers

warnings.filterwarnings('ignore', category = FutureWarning, module = 'insightface')
warnings.filterwarnings('ignore', category = UserWarning, module = 'torchvision')


def parse_args() -> None:
	signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
	program = argparse.ArgumentParser(formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position = 120))
	program.add_argument('-s', '--source', help = wording.get('source_help'), dest = 'source_path')
	program.add_argument('-t', '--target', help = wording.get('target_help'), dest = 'target_path')
	program.add_argument('-o', '--output', help = wording.get('output_help'), dest = 'output_path')
	program.add_argument('--frame-processors', help = wording.get('frame_processors_help').format(choices = ', '.join(list_module_names('facefusion/processors/frame/modules'))), dest = 'frame_processors', default = ['face_swapper'], nargs = '+')
	program.add_argument('--ui-layouts', help = wording.get('ui_layouts_help').format(choices = ', '.join(list_module_names('facefusion/uis/layouts'))), dest = 'ui_layouts', default = ['default'], nargs = '+')
	program.add_argument('--keep-fps', help = wording.get('keep_fps_help'), dest = 'keep_fps', action = 'store_true')
	program.add_argument('--keep-temp', help = wording.get('keep_temp_help'), dest = 'keep_temp', action = 'store_true')
	program.add_argument('--skip-audio', help = wording.get('skip_audio_help'), dest = 'skip_audio', action = 'store_true')
	program.add_argument('--face-recognition', help = wording.get('face_recognition_help'), dest = 'face_recognition', default = 'reference', choices = facefusion.choices.face_recognition)
	program.add_argument('--face-analyser-direction', help = wording.get('face_analyser_direction_help'), dest = 'face_analyser_direction', default = 'left-right', choices = facefusion.choices.face_analyser_direction)
	program.add_argument('--face-analyser-age', help = wording.get('face_analyser_age_help'), dest = 'face_analyser_age', choices = facefusion.choices.face_analyser_age)
	program.add_argument('--face-analyser-gender', help = wording.get('face_analyser_gender_help'), dest = 'face_analyser_gender', choices = facefusion.choices.face_analyser_gender)
	program.add_argument('--reference-face-position', help = wording.get('reference_face_position_help'), dest = 'reference_face_position', type = int, default = 0)
	program.add_argument('--reference-face-distance', help = wording.get('reference_face_distance_help'), dest = 'reference_face_distance', type = float, default = 1.5)
	program.add_argument('--reference-frame-number', help = wording.get('reference_frame_number_help'), dest = 'reference_frame_number', type = int, default = 0)
	program.add_argument('--trim-frame-start', help = wording.get('trim_frame_start_help'), dest = 'trim_frame_start', type = int)
	program.add_argument('--trim-frame-end', help = wording.get('trim_frame_end_help'), dest = 'trim_frame_end', type = int)
	program.add_argument('--temp-frame-format', help = wording.get('temp_frame_format_help'), dest = 'temp_frame_format', default = 'jpg', choices = facefusion.choices.temp_frame_format)
	program.add_argument('--temp-frame-quality', help = wording.get('temp_frame_quality_help'), dest = 'temp_frame_quality', type = int, default = 100, choices = range(101), metavar = '[0-100]')
	program.add_argument('--output-image-quality', help=wording.get('output_image_quality_help'), dest = 'output_image_quality', type = int, default = 90, choices = range(101), metavar = '[0-100]')
	program.add_argument('--output-video-encoder', help = wording.get('output_video_encoder_help'), dest = 'output_video_encoder', default = 'libx264', choices = facefusion.choices.output_video_encoder)
	program.add_argument('--output-video-quality', help = wording.get('output_video_quality_help'), dest = 'output_video_quality', type = int, default = 90, choices = range(101), metavar = '[0-100]')
	program.add_argument('--max-memory', help = wording.get('max_memory_help'), dest = 'max_memory', type = int)
	program.add_argument('--execution-providers', help = wording.get('execution_providers_help').format(choices = 'cpu'), dest = 'execution_providers', default = ['cpu'], choices = suggest_execution_providers_choices(), nargs = '+')
	program.add_argument('--execution-thread-count', help = wording.get('execution_thread_count_help'), dest = 'execution_thread_count', type = int, default = suggest_execution_thread_count_default())
	program.add_argument('--execution-queue-count', help = wording.get('execution_queue_count_help'), dest = 'execution_queue_count', type = int, default = 1)
	program.add_argument('--skip-download', help = wording.get('skip_download_help'), dest = 'skip_download', action = 'store_true')
	program.add_argument('--headless', help = wording.get('headless_help'), dest = 'headless', action = 'store_true')
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')

	args = program.parse_args()

	facefusion.globals.source_path = args.source_path
	facefusion.globals.target_path = args.target_path
	facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, args.output_path)
	facefusion.globals.frame_processors = args.frame_processors
	facefusion.globals.ui_layouts = args.ui_layouts
	facefusion.globals.keep_fps = args.keep_fps
	facefusion.globals.keep_temp = args.keep_temp
	facefusion.globals.skip_audio = args.skip_audio
	facefusion.globals.face_recognition = args.face_recognition
	facefusion.globals.face_analyser_direction = args.face_analyser_direction
	facefusion.globals.face_analyser_age = args.face_analyser_age
	facefusion.globals.face_analyser_gender = args.face_analyser_gender
	facefusion.globals.reference_face_position = args.reference_face_position
	facefusion.globals.reference_frame_number = args.reference_frame_number
	facefusion.globals.reference_face_distance = args.reference_face_distance
	facefusion.globals.trim_frame_start = args.trim_frame_start
	facefusion.globals.trim_frame_end = args.trim_frame_end
	facefusion.globals.temp_frame_format = args.temp_frame_format
	facefusion.globals.temp_frame_quality = args.temp_frame_quality
	facefusion.globals.output_image_quality = args.output_image_quality
	facefusion.globals.output_video_encoder = args.output_video_encoder
	facefusion.globals.output_video_quality = args.output_video_quality
	facefusion.globals.max_memory = args.max_memory
	facefusion.globals.execution_providers = decode_execution_providers(args.execution_providers)
	facefusion.globals.execution_thread_count = args.execution_thread_count
	facefusion.globals.execution_queue_count = args.execution_queue_count
	facefusion.globals.skip_download = args.skip_download
	facefusion.globals.headless = args.headless


def suggest_execution_providers_choices() -> List[str]:
	return encode_execution_providers(onnxruntime.get_available_providers())


def suggest_execution_thread_count_default() -> int:
	if 'CUDAExecutionProvider' in onnxruntime.get_available_providers():
		return 8
	return 1


def limit_resources() -> None:
	# prevent tensorflow memory leak
	gpus = tensorflow.config.experimental.list_physical_devices('GPU')
	for gpu in gpus:
		tensorflow.config.experimental.set_virtual_device_configuration(gpu, [
			tensorflow.config.experimental.VirtualDeviceConfiguration(memory_limit = 512)
		])
	# limit memory usage
	if facefusion.globals.max_memory:
		memory = facefusion.globals.max_memory * 1024 ** 3
		if platform.system().lower() == 'darwin':
			memory = facefusion.globals.max_memory * 1024 ** 6
		if platform.system().lower() == 'windows':
			import ctypes
			kernel32 = ctypes.windll.kernel32 # type: ignore[attr-defined]
			kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
		else:
			import resource
			resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def update_status(message : str, scope : str = 'FACEFUSION.CORE') -> None:
	print('[' + scope + '] ' + message)


def pre_check() -> bool:
	if sys.version_info < (3, 9):
		update_status(wording.get('python_not_supported').format(version = '3.9'))
		return False
	if not shutil.which('ffmpeg'):
		update_status(wording.get('ffmpeg_not_installed'))
		return False
	return True


def process_image() -> None:
	if predict_image(facefusion.globals.target_path):
		return
	shutil.copy2(facefusion.globals.target_path, facefusion.globals.output_path)
	# process frame
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		update_status(wording.get('processing'), frame_processor_module.NAME)
		frame_processor_module.process_image(facefusion.globals.source_path, facefusion.globals.output_path, facefusion.globals.output_path)
		frame_processor_module.post_process()
	# compress image
	update_status(wording.get('compressing_image'))
	if not compress_image(facefusion.globals.output_path):
		update_status(wording.get('compressing_image_failed'))
	# validate image
	if is_image(facefusion.globals.target_path):
		update_status(wording.get('processing_image_succeed'))
	else:
		update_status(wording.get('processing_image_failed'))


def process_video() -> None:
	if predict_video(facefusion.globals.target_path):
		return
	fps = detect_fps(facefusion.globals.target_path) if facefusion.globals.keep_fps else 25.0
	update_status(wording.get('creating_temp'))
	create_temp(facefusion.globals.target_path)
	# extract frames
	update_status(wording.get('extracting_frames_fps').format(fps = fps))
	extract_frames(facefusion.globals.target_path, fps)
	# process frame
	temp_frame_paths = get_temp_frame_paths(facefusion.globals.target_path)
	if temp_frame_paths:
		for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
			update_status(wording.get('processing'), frame_processor_module.NAME)
			frame_processor_module.process_video(facefusion.globals.source_path, temp_frame_paths)
			frame_processor_module.post_process()
	else:
		update_status(wording.get('temp_frames_not_found'))
		return
	# merge video
	update_status(wording.get('merging_video_fps').format(fps = fps))
	if not merge_video(facefusion.globals.target_path, fps):
		update_status(wording.get('merging_video_failed'))
		return
	# handle audio
	if facefusion.globals.skip_audio:
		update_status(wording.get('skipping_audio'))
		move_temp(facefusion.globals.target_path, facefusion.globals.output_path)
	else:
		update_status(wording.get('restoring_audio'))
		if not restore_audio(facefusion.globals.target_path, facefusion.globals.output_path):
			update_status(wording.get('restoring_audio_failed'))
			move_temp(facefusion.globals.target_path, facefusion.globals.output_path)
	# clear temp
	update_status(wording.get('clearing_temp'))
	clear_temp(facefusion.globals.target_path)
	# validate video
	if is_video(facefusion.globals.target_path):
		update_status(wording.get('processing_video_succeed'))
	else:
		update_status(wording.get('processing_video_failed'))


def conditional_process() -> None:
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		if not frame_processor_module.pre_process('output'):
			return
	if is_image(facefusion.globals.target_path):
		process_image()
	if is_video(facefusion.globals.target_path):
		process_video()


def run() -> None:
	parse_args()
	limit_resources()
	# pre check
	if not pre_check():
		return
	for frame_processor in get_frame_processors_modules(facefusion.globals.frame_processors):
		if not frame_processor.pre_check():
			return
	# headless or ui
	if facefusion.globals.headless:
		conditional_process()
	else:
		import facefusion.uis.core as ui

		# pre check
		for ui_layout in ui.get_ui_layouts_modules(facefusion.globals.ui_layouts):
			if not ui_layout.pre_check():
				return
		ui.launch()


def destroy() -> None:
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	sys.exit()
