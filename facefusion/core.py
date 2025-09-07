import inspect
import itertools
import shutil
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

import numpy
from tqdm import tqdm

from facefusion import benchmarker, cli_helper, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, hash_helper, logger, process_manager, state_manager, video_manager, voice_extractor, wording
from facefusion.args import apply_args, collect_job_args, reduce_job_args, reduce_step_args
from facefusion.audio import create_empty_audio_frame, get_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.content_analyser import analyse_image, analyse_video
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.exit_helper import hard_exit, signal_exit
from facefusion.ffmpeg import copy_image, extract_frames, finalize_image, merge_video, replace_audio, restore_audio
from facefusion.filesystem import filter_audio_paths, get_file_name, is_image, is_video, resolve_file_paths, resolve_file_pattern
from facefusion.jobs import job_helper, job_manager, job_runner
from facefusion.jobs.job_list import compose_job_list
from facefusion.memory import limit_system_memory
from facefusion.processors.core import get_processors_modules
from facefusion.program import create_program
from facefusion.program_helper import validate_args
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, move_temp_file, resolve_temp_frame_paths
from facefusion.time_helper import calculate_end_time
from facefusion.types import Args, ErrorCode
from facefusion.vision import detect_image_resolution, detect_video_resolution, pack_resolution, read_static_image, read_static_images, read_static_video_frame, restrict_image_resolution, restrict_trim_frame, restrict_video_fps, restrict_video_resolution, scale_resolution, write_image


def cli() -> None:
	if pre_check():
		signal.signal(signal.SIGINT, signal_exit)
		program = create_program()

		if validate_args(program):
			args = vars(program.parse_args())
			apply_args(args, state_manager.init_item)

			if state_manager.get_item('command'):
				logger.init(state_manager.get_item('log_level'))
				route(args)
			else:
				program.print_help()
		else:
			hard_exit(2)
	else:
		hard_exit(2)


def route(args : Args) -> None:
	system_memory_limit = state_manager.get_item('system_memory_limit')

	if system_memory_limit and system_memory_limit > 0:
		limit_system_memory(system_memory_limit)

	if state_manager.get_item('command') == 'force-download':
		error_code = force_download()
		hard_exit(error_code)

	if state_manager.get_item('command') == 'benchmark':
		if not common_pre_check() or not processors_pre_check() or not benchmarker.pre_check():
			hard_exit(2)
		benchmarker.render()

	if state_manager.get_item('command') in [ 'job-list', 'job-create', 'job-submit', 'job-submit-all', 'job-delete', 'job-delete-all', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]:
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_code = route_job_manager(args)
		hard_exit(error_code)

	if state_manager.get_item('command') == 'run':
		import facefusion.uis.core as ui

		if not common_pre_check() or not processors_pre_check():
			hard_exit(2)
		for ui_layout in ui.get_ui_layouts_modules(state_manager.get_item('ui_layouts')):
			if not ui_layout.pre_check():
				hard_exit(2)
		ui.init()
		ui.launch()

	if state_manager.get_item('command') == 'headless-run':
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_core = process_headless(args)
		hard_exit(error_core)

	if state_manager.get_item('command') == 'batch-run':
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_core = process_batch(args)
		hard_exit(error_core)

	if state_manager.get_item('command') in [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]:
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_code = route_job_runner()
		hard_exit(error_code)


def pre_check() -> bool:
	if sys.version_info < (3, 10):
		logger.error(wording.get('python_not_supported').format(version = '3.10'), __name__)
		return False

	if not shutil.which('curl'):
		logger.error(wording.get('curl_not_installed'), __name__)
		return False

	if not shutil.which('ffmpeg'):
		logger.error(wording.get('ffmpeg_not_installed'), __name__)
		return False
	return True


def common_pre_check() -> bool:
	common_modules =\
	[
		content_analyser,
		face_classifier,
		face_detector,
		face_landmarker,
		face_masker,
		face_recognizer,
		voice_extractor
	]

	content_analyser_content = inspect.getsource(content_analyser).encode()
	content_analyser_hash = hash_helper.create_hash(content_analyser_content)

	return all(module.pre_check() for module in common_modules) and content_analyser_hash == '803b5ec7'


def processors_pre_check() -> bool:
	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		if not processor_module.pre_check():
			return False
	return True


def force_download() -> ErrorCode:
	common_modules =\
	[
		content_analyser,
		face_classifier,
		face_detector,
		face_landmarker,
		face_masker,
		face_recognizer,
		voice_extractor
	]
	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/processors/modules') ]
	processor_modules = get_processors_modules(available_processors)

	for module in common_modules + processor_modules:
		if hasattr(module, 'create_static_model_set'):
			for model in module.create_static_model_set(state_manager.get_item('download_scope')).values():
				model_hash_set = model.get('hashes')
				model_source_set = model.get('sources')

				if model_hash_set and model_source_set:
					if not conditional_download_hashes(model_hash_set) or not conditional_download_sources(model_source_set):
						return 1

	return 0


def route_job_manager(args : Args) -> ErrorCode:
	if state_manager.get_item('command') == 'job-list':
		job_headers, job_contents = compose_job_list(state_manager.get_item('job_status'))

		if job_contents:
			cli_helper.render_table(job_headers, job_contents)
			return 0
		return 1

	if state_manager.get_item('command') == 'job-create':
		if job_manager.create_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_created').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(wording.get('job_not_created').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-submit':
		if job_manager.submit_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_submitted').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(wording.get('job_not_submitted').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-submit-all':
		if job_manager.submit_jobs(state_manager.get_item('halt_on_error')):
			logger.info(wording.get('job_all_submitted'), __name__)
			return 0
		logger.error(wording.get('job_all_not_submitted'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-delete':
		if job_manager.delete_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_deleted').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(wording.get('job_not_deleted').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-delete-all':
		if job_manager.delete_jobs(state_manager.get_item('halt_on_error')):
			logger.info(wording.get('job_all_deleted'), __name__)
			return 0
		logger.error(wording.get('job_all_not_deleted'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-add-step':
		step_args = reduce_step_args(args)

		if job_manager.add_step(state_manager.get_item('job_id'), step_args):
			logger.info(wording.get('job_step_added').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(wording.get('job_step_not_added').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-remix-step':
		step_args = reduce_step_args(args)

		if job_manager.remix_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(wording.get('job_remix_step_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(wording.get('job_remix_step_not_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-insert-step':
		step_args = reduce_step_args(args)

		if job_manager.insert_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(wording.get('job_step_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(wording.get('job_step_not_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-remove-step':
		if job_manager.remove_step(state_manager.get_item('job_id'), state_manager.get_item('step_index')):
			logger.info(wording.get('job_step_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(wording.get('job_step_not_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1
	return 1


def route_job_runner() -> ErrorCode:
	if state_manager.get_item('command') == 'job-run':
		logger.info(wording.get('running_job').format(job_id = state_manager.get_item('job_id')), __name__)
		if job_runner.run_job(state_manager.get_item('job_id'), process_step):
			logger.info(wording.get('processing_job_succeeded').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-run-all':
		logger.info(wording.get('running_jobs'), __name__)
		if job_runner.run_jobs(process_step, state_manager.get_item('halt_on_error')):
			logger.info(wording.get('processing_jobs_succeeded'), __name__)
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-retry':
		logger.info(wording.get('retrying_job').format(job_id = state_manager.get_item('job_id')), __name__)
		if job_runner.retry_job(state_manager.get_item('job_id'), process_step):
			logger.info(wording.get('processing_job_succeeded').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-retry-all':
		logger.info(wording.get('retrying_jobs'), __name__)
		if job_runner.retry_jobs(process_step, state_manager.get_item('halt_on_error')):
			logger.info(wording.get('processing_jobs_succeeded'), __name__)
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__)
		return 1
	return 2


def process_headless(args : Args) -> ErrorCode:
	job_id = job_helper.suggest_job_id('headless')
	step_args = reduce_step_args(args)

	if job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
		return 0
	return 1


def process_batch(args : Args) -> ErrorCode:
	job_id = job_helper.suggest_job_id('batch')
	step_args = reduce_step_args(args)
	job_args = reduce_job_args(args)
	source_paths = resolve_file_pattern(job_args.get('source_pattern'))
	target_paths = resolve_file_pattern(job_args.get('target_pattern'))

	if job_manager.create_job(job_id):
		if source_paths and target_paths:
			for index, (source_path, target_path) in enumerate(itertools.product(source_paths, target_paths)):
				step_args['source_paths'] = [ source_path ]
				step_args['target_path'] = target_path
				step_args['output_path'] = job_args.get('output_pattern').format(index = index)
				if not job_manager.add_step(job_id, step_args):
					return 1
			if job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
				return 0

		if not source_paths and target_paths:
			for index, target_path in enumerate(target_paths):
				step_args['target_path'] = target_path
				step_args['output_path'] = job_args.get('output_pattern').format(index = index)
				if not job_manager.add_step(job_id, step_args):
					return 1
			if job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
				return 0
	return 1


def process_step(job_id : str, step_index : int, step_args : Args) -> bool:
	step_total = job_manager.count_step_total(job_id)
	step_args.update(collect_job_args())
	apply_args(step_args, state_manager.set_item)

	logger.info(wording.get('processing_step').format(step_current = step_index + 1, step_total = step_total), __name__)
	if common_pre_check() and processors_pre_check():
		error_code = conditional_process()
		return error_code == 0
	return False


def conditional_process() -> ErrorCode:
	start_time = time()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		if not processor_module.pre_process('output'):
			return 2

	if is_image(state_manager.get_item('target_path')):
		return process_image(start_time)
	if is_video(state_manager.get_item('target_path')):
		return process_video(start_time)

	return 0


def process_image(start_time : float) -> ErrorCode:
	if analyse_image(state_manager.get_item('target_path')):
		return 3

	logger.debug(wording.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))
	logger.debug(wording.get('creating_temp'), __name__)
	create_temp_directory(state_manager.get_item('target_path'))

	process_manager.start()

	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_image_resolution = restrict_image_resolution(state_manager.get_item('target_path'), output_image_resolution)
	logger.info(wording.get('copying_image').format(resolution = pack_resolution(temp_image_resolution)), __name__)
	if copy_image(state_manager.get_item('target_path'), temp_image_resolution):
		logger.debug(wording.get('copying_image_succeeded'), __name__)
	else:
		logger.error(wording.get('copying_image_failed'), __name__)
		process_manager.end()
		return 1

	temp_image_path = get_temp_file_path(state_manager.get_item('target_path'))
	reference_vision_frame = read_static_image(temp_image_path)
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	target_vision_frame = read_static_image(temp_image_path)
	temp_vision_frame = target_vision_frame.copy()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.info(wording.get('processing'), processor_module.__name__)

		temp_vision_frame = processor_module.process_frame(
		{
			'reference_vision_frame': reference_vision_frame,
			'source_vision_frames': source_vision_frames,
			'source_audio_frame': source_audio_frame,
			'source_voice_frame': source_voice_frame,
			'target_vision_frame': target_vision_frame,
			'temp_vision_frame': temp_vision_frame
		})

		processor_module.post_process()

	write_image(temp_image_path, temp_vision_frame)
	if is_process_stopping():
		return 4

	logger.info(wording.get('finalizing_image').format(resolution = pack_resolution(output_image_resolution)), __name__)
	if finalize_image(state_manager.get_item('target_path'), state_manager.get_item('output_path'), output_image_resolution):
		logger.debug(wording.get('finalizing_image_succeeded'), __name__)
	else:
		logger.warn(wording.get('finalizing_image_skipped'), __name__)

	logger.debug(wording.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))

	if is_image(state_manager.get_item('output_path')):
		logger.info(wording.get('processing_image_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(wording.get('processing_image_failed'), __name__)
		process_manager.end()
		return 1
	process_manager.end()
	return 0


def process_video(start_time : float) -> ErrorCode:
	trim_frame_start, trim_frame_end = restrict_trim_frame(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end'))
	if analyse_video(state_manager.get_item('target_path'), trim_frame_start, trim_frame_end):
		return 3

	logger.debug(wording.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))
	logger.debug(wording.get('creating_temp'), __name__)
	create_temp_directory(state_manager.get_item('target_path'))

	process_manager.start()
	output_video_resolution = scale_resolution(detect_video_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_video_scale'))
	temp_video_resolution = restrict_video_resolution(state_manager.get_item('target_path'), output_video_resolution)
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	logger.info(wording.get('extracting_frames').format(resolution = pack_resolution(temp_video_resolution), fps = temp_video_fps), __name__)

	if extract_frames(state_manager.get_item('target_path'), temp_video_resolution, temp_video_fps, trim_frame_start, trim_frame_end):
		logger.debug(wording.get('extracting_frames_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(wording.get('extracting_frames_failed'), __name__)
		process_manager.end()
		return 1

	temp_frame_paths = resolve_temp_frame_paths(state_manager.get_item('target_path'))

	if temp_frame_paths:
		with tqdm(total = len(temp_frame_paths), desc = wording.get('processing'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
			progress.set_postfix(execution_providers = state_manager.get_item('execution_providers'))

			with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
				futures = []

				for frame_number, temp_frame_path in enumerate(temp_frame_paths):
					future = executor.submit(process_temp_frame, temp_frame_path, frame_number)
					futures.append(future)

				for future in as_completed(futures):
					if is_process_stopping():
						for __future__ in futures:
							__future__.cancel()

					if not future.cancelled():
						future.result()
						progress.update()

		for processor_module in get_processors_modules(state_manager.get_item('processors')):
			processor_module.post_process()

		if is_process_stopping():
			return 4
	else:
		logger.error(wording.get('temp_frames_not_found'), __name__)
		process_manager.end()
		return 1

	logger.info(wording.get('merging_video').format(resolution = pack_resolution(output_video_resolution), fps = state_manager.get_item('output_video_fps')), __name__)
	if merge_video(state_manager.get_item('target_path'), temp_video_fps, output_video_resolution, state_manager.get_item('output_video_fps'), trim_frame_start, trim_frame_end):
		logger.debug(wording.get('merging_video_succeeded'), __name__)
	else:
		if is_process_stopping():
			return 4
		logger.error(wording.get('merging_video_failed'), __name__)
		process_manager.end()
		return 1

	if state_manager.get_item('output_audio_volume') == 0:
		logger.info(wording.get('skipping_audio'), __name__)
		move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
	else:
		source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
		if source_audio_path:
			if replace_audio(state_manager.get_item('target_path'), source_audio_path, state_manager.get_item('output_path')):
				video_manager.clear_video_pool()
				logger.debug(wording.get('replacing_audio_succeeded'), __name__)
			else:
				video_manager.clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(wording.get('replacing_audio_skipped'), __name__)
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
		else:
			if restore_audio(state_manager.get_item('target_path'), state_manager.get_item('output_path'), trim_frame_start, trim_frame_end):
				video_manager.clear_video_pool()
				logger.debug(wording.get('restoring_audio_succeeded'), __name__)
			else:
				video_manager.clear_video_pool()
				if is_process_stopping():
					return 4
				logger.warn(wording.get('restoring_audio_skipped'), __name__)
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))

	logger.debug(wording.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))

	if is_video(state_manager.get_item('output_path')):
		logger.info(wording.get('processing_video_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(wording.get('processing_video_failed'), __name__)
		process_manager.end()
		return 1
	process_manager.end()
	return 0


def process_temp_frame(temp_frame_path : str, frame_number : int) -> bool:
	reference_vision_frame = read_static_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	target_vision_frame = read_static_image(temp_frame_path)
	temp_vision_frame = target_vision_frame.copy()

	source_audio_frame = get_audio_frame(source_audio_path, temp_video_fps, frame_number)
	source_voice_frame = get_voice_frame(source_audio_path, temp_video_fps, frame_number)

	if not numpy.any(source_audio_frame):
		source_audio_frame = create_empty_audio_frame()
	if not numpy.any(source_voice_frame):
		source_voice_frame = create_empty_audio_frame()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		temp_vision_frame = processor_module.process_frame(
		{
			'reference_vision_frame': reference_vision_frame,
			'source_vision_frames': source_vision_frames,
			'source_audio_frame': source_audio_frame,
			'source_voice_frame': source_voice_frame,
			'target_vision_frame': target_vision_frame,
			'temp_vision_frame': temp_vision_frame
		})

	return write_image(temp_frame_path, temp_vision_frame)


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__)
	return process_manager.is_pending()
