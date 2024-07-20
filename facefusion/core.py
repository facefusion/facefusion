import shutil
import signal
import sys
from time import sleep, time

import numpy
import onnxruntime

from facefusion import content_analyser, face_analyser, face_masker, logger, process_manager, state_manager, voice_extractor, wording
from facefusion.args import apply_args, collect_job_args, reduce_step_args
from facefusion.common_helper import get_first
from facefusion.content_analyser import analyse_image, analyse_video
from facefusion.download import conditional_download
from facefusion.exit_helper import conditional_exit, graceful_exit, hard_exit
from facefusion.face_analyser import get_average_face, get_many_faces, get_one_face
from facefusion.face_selector import sort_and_filter_faces
from facefusion.face_store import append_reference_face, get_reference_faces
from facefusion.ffmpeg import copy_image, extract_frames, finalize_image, merge_video, replace_audio, restore_audio
from facefusion.filesystem import filter_audio_paths, is_image, is_video, list_directory, resolve_relative_path
from facefusion.jobs import job_helper, job_manager, job_runner
from facefusion.jobs.job_list import compose_job_list
from facefusion.memory import limit_system_memory
from facefusion.processors.frame.core import clear_frame_processors_modules, get_frame_processors_modules
from facefusion.program import create_program
from facefusion.program_helper import validate_args
from facefusion.statistics import conditional_log_statistics
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path, get_temp_frame_paths, move_temp_file
from facefusion.typing import Args, ErrorCode
from facefusion.vision import get_video_frame, pack_resolution, read_image, read_static_images, restrict_image_resolution, restrict_video_fps, restrict_video_resolution, unpack_resolution

onnxruntime.set_default_logger_severity(3)


def cli() -> None:
	signal.signal(signal.SIGINT, lambda signal_number, frame: graceful_exit(0))
	program = create_program()

	if validate_args(program):
		args = vars(program.parse_args())
		apply_args(args)

		if state_manager.get_item('command'):
			logger.init(state_manager.get_item('log_level'))
			run(args)
		else:
			program.print_help()


def run(args : Args) -> None:
	system_memory_limit = state_manager.get_item('system_memory_limit')
	if system_memory_limit and system_memory_limit > 0:
		limit_system_memory(system_memory_limit)
	if state_manager.get_item('command') == 'force-download':
		force_download()
		return conditional_exit(0)
	if state_manager.get_item('command') in [ 'job-create', 'job-submit', 'job-submit-all', 'job-delete', 'job-delete-all', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step', 'job-list' ]:
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_code = route_job_manager(args)
		hard_exit(error_code)
	if not pre_check():
		return conditional_exit(2)
	if state_manager.get_item('command') in [ 'run', 'run-headless' ]:
		if not content_analyser.pre_check() or not face_analyser.pre_check() or not face_masker.pre_check() or not voice_extractor.pre_check():
			return conditional_exit(2)
		for frame_processor_module in get_frame_processors_modules(state_manager.get_item('frame_processors')):
			if not frame_processor_module.pre_check():
				return conditional_exit(2)
	if state_manager.get_item('command') == 'run':
		import facefusion.uis.core as ui

		for ui_layout in ui.get_ui_layouts_modules(state_manager.get_item('ui_layouts')):
			if not ui_layout.pre_check():
				return conditional_exit(2)
		ui.launch()
	if state_manager.get_item('command') == 'run-headless':
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_core = process_headless(args)
		hard_exit(error_core)
	if state_manager.get_item('command') in [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]:
		if not job_manager.init_jobs(state_manager.get_item('jobs_path')):
			hard_exit(1)
		error_code = route_job_runner()
		hard_exit(error_code)


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
	for frame_processor_module in get_frame_processors_modules(state_manager.get_item('frame_processors')):
		while not frame_processor_module.post_check():
			logger.disable()
			sleep(0.5)
		logger.enable()
		if not frame_processor_module.pre_process('output'):
			return 2
	conditional_append_reference_faces()
	if is_image(state_manager.get_item('target_path')):
		return process_image(start_time)
	if is_video(state_manager.get_item('target_path')):
		return process_video(start_time)
	return 0


def conditional_append_reference_faces() -> None:
	if 'reference' in state_manager.get_item('face_selector_mode') and not get_reference_faces():
		source_frames = read_static_images(state_manager.get_item('source_paths'))
		source_faces = get_many_faces(source_frames)
		source_face = get_average_face(source_faces)
		if is_video(state_manager.get_item('target_path')):
			reference_frame = get_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		else:
			reference_frame = read_image(state_manager.get_item('target_path'))
		reference_faces = sort_and_filter_faces(get_many_faces([ reference_frame ]))
		reference_face = get_one_face(reference_faces, state_manager.get_item('reference_face_position'))
		append_reference_face('origin', reference_face)

		if source_face and reference_face:
			for frame_processor_module in get_frame_processors_modules(state_manager.get_item('frame_processors')):
				abstract_reference_frame = frame_processor_module.get_reference_frame(source_face, reference_face, reference_frame)
				if numpy.any(abstract_reference_frame):
					abstract_reference_faces = sort_and_filter_faces(get_many_faces([ abstract_reference_frame]))
					abstract_reference_face = get_one_face(abstract_reference_faces, state_manager.get_item('reference_face_position'))
					append_reference_face(frame_processor_module.__name__, abstract_reference_face)


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


def route_job_manager(args : Args) -> ErrorCode:
	if state_manager.get_item('command') == 'job-create':
		if job_manager.create_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_created').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.error(wording.get('job_not_created').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-submit':
		if job_manager.submit_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_submitted').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.error(wording.get('job_not_submitted').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-submit-all':
		if job_manager.submit_jobs():
			logger.info(wording.get('job_all_submitted'), __name__.upper())
			return 0
		logger.error(wording.get('job_all_not_submitted'), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-delete':
		if job_manager.delete_job(state_manager.get_item('job_id')):
			logger.info(wording.get('job_deleted').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.error(wording.get('job_not_deleted').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-delete-all':
		if job_manager.delete_jobs():
			logger.info(wording.get('job_all_deleted'), __name__.upper())
			return 0
		logger.error(wording.get('job_all_not_deleted'), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-list':
		job_headers, job_contents = compose_job_list(state_manager.get_item('job_status'))

		if job_contents:
			logger.table(job_headers, job_contents)
			return 0
		return 1
	if state_manager.get_item('command') == 'job-add-step':
		step_args = reduce_step_args(args)

		if job_manager.add_step(state_manager.get_item('job_id'), step_args):
			logger.info(wording.get('job_step_added').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_added').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-remix-step':
		step_args = reduce_step_args(args)

		if job_manager.remix_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(wording.get('job_remix_step_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
			return 0
		logger.error(wording.get('job_remix_step_not_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-insert-step':
		step_args = reduce_step_args(args)

		if job_manager.insert_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(wording.get('job_step_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-remove-step':
		if job_manager.remove_step(state_manager.get_item('job_id'), state_manager.get_item('step_index')):
			logger.info(wording.get('job_step_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
			return 0
		logger.error(wording.get('job_step_not_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__.upper())
		return 1
	return 1


def route_job_runner() -> ErrorCode:
	if state_manager.get_item('command') == 'job-run':
		logger.info(wording.get('running_job').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		if job_runner.run_job(state_manager.get_item('job_id'), process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-run-all':
		logger.info(wording.get('running_jobs'), __name__.upper())
		if job_runner.run_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-retry':
		logger.info(wording.get('retrying_job').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		if job_runner.retry_job(state_manager.get_item('job_id'), process_step):
			logger.info(wording.get('processing_job_succeed').format(job_id = state_manager.get_item('job_id')), __name__.upper())
			return 0
		logger.info(wording.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__.upper())
		return 1
	if state_manager.get_item('command') == 'job-retry-all':
		logger.info(wording.get('retrying_jobs'), __name__.upper())
		if job_runner.retry_jobs(process_step):
			logger.info(wording.get('processing_jobs_succeed'), __name__.upper())
			return 0
		logger.info(wording.get('processing_jobs_failed'), __name__.upper())
		return 1
	return 2


def process_step(job_id : str, step_index : int, step_args : Args) -> bool:
	args = step_args
	args.update(collect_job_args())
	step_total = job_manager.count_step_total(job_id)
	logger.info(wording.get('processing_step').format(step_current = step_index + 1, step_total = step_total), __name__.upper())
	apply_args(args)
	clear_frame_processors_modules()
	error_code = conditional_process()
	return error_code == 0


def process_headless(args : Args) -> ErrorCode:
	job_id = job_helper.suggest_job_id('headless')
	step_args = reduce_step_args(args)

	if job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
		return 0
	return 1


def process_image(start_time : float) -> ErrorCode:
	if analyse_image(state_manager.get_item('target_path')):
		return 3
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(state_manager.get_item('target_path'))
	# create temp
	logger.debug(wording.get('creating_temp'), __name__.upper())
	create_temp_directory(state_manager.get_item('target_path'))
	# copy image
	process_manager.start()
	temp_image_resolution = pack_resolution(restrict_image_resolution(state_manager.get_item('target_path'), unpack_resolution(state_manager.get_item('output_image_resolution'))))
	logger.info(wording.get('copying_image').format(resolution = temp_image_resolution), __name__.upper())
	if copy_image(state_manager.get_item('target_path'), temp_image_resolution):
		logger.debug(wording.get('copying_image_succeed'), __name__.upper())
	else:
		logger.error(wording.get('copying_image_failed'), __name__.upper())
		process_manager.end()
		return 1
	# process image
	temp_file_path = get_temp_file_path(state_manager.get_item('target_path'))
	for frame_processor_module in get_frame_processors_modules(state_manager.get_item('frame_processors')):
		logger.info(wording.get('processing'), frame_processor_module.NAME)
		frame_processor_module.process_image(state_manager.get_item('source_paths'), temp_file_path, temp_file_path)
		frame_processor_module.post_process()
	if is_process_stopping():
		process_manager.end()
		return 4
	# finalize image
	logger.info(wording.get('finalizing_image').format(resolution = state_manager.get_item('output_image_resolution')), __name__.upper())
	if finalize_image(state_manager.get_item('target_path'), state_manager.get_item('output_path'), state_manager.get_item('output_image_resolution')):
		logger.debug(wording.get('finalizing_image_succeed'), __name__.upper())
	else:
		logger.warn(wording.get('finalizing_image_skipped'), __name__.upper())
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(state_manager.get_item('target_path'))
	# validate image
	if is_image(state_manager.get_item('output_path')):
		seconds = '{:.2f}'.format((time() - start_time) % 60)
		logger.info(wording.get('processing_image_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_image_failed'), __name__.upper())
		process_manager.end()
		return 1
	process_manager.end()
	return 0


def process_video(start_time : float) -> ErrorCode:
	if analyse_video(state_manager.get_item('target_path'), state_manager.get_item('trim_frame_start'), state_manager.get_item('trim_frame_end')):
		return 3
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(state_manager.get_item('target_path'))
	# create temp
	logger.debug(wording.get('creating_temp'), __name__.upper())
	create_temp_directory(state_manager.get_item('target_path'))
	# extract frames
	process_manager.start()
	temp_video_resolution = pack_resolution(restrict_video_resolution(state_manager.get_item('target_path'), unpack_resolution(state_manager.get_item('output_video_resolution'))))
	temp_video_fps = restrict_video_fps(state_manager.get_item('target_path'), state_manager.get_item('output_video_fps'))
	logger.info(wording.get('extracting_frames').format(resolution = temp_video_resolution, fps = temp_video_fps), __name__.upper())
	if extract_frames(state_manager.get_item('target_path'), temp_video_resolution, temp_video_fps):
		logger.debug(wording.get('extracting_frames_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			process_manager.end()
			return 4
		logger.error(wording.get('extracting_frames_failed'), __name__.upper())
		process_manager.end()
		return 1
	# process frames
	temp_frame_paths = get_temp_frame_paths(state_manager.get_item('target_path'))
	if temp_frame_paths:
		for frame_processor_module in get_frame_processors_modules(state_manager.get_item('frame_processors')):
			logger.info(wording.get('processing'), frame_processor_module.NAME)
			frame_processor_module.process_video(state_manager.get_item('source_paths'), temp_frame_paths)
			frame_processor_module.post_process()
		if is_process_stopping():
			return 4
	else:
		logger.error(wording.get('temp_frames_not_found'), __name__.upper())
		process_manager.end()
		return 1
	# merge video
	logger.info(wording.get('merging_video').format(resolution = state_manager.get_item('output_video_resolution'), fps = state_manager.get_item('output_video_fps')), __name__.upper())
	if merge_video(state_manager.get_item('target_path'), state_manager.get_item('output_video_resolution'), state_manager.get_item('output_video_fps')):
		logger.debug(wording.get('merging_video_succeed'), __name__.upper())
	else:
		if is_process_stopping():
			process_manager.end()
			return 4
		logger.error(wording.get('merging_video_failed'), __name__.upper())
		process_manager.end()
		return 1
	# handle audio
	if state_manager.get_item('skip_audio'):
		logger.info(wording.get('skipping_audio'), __name__.upper())
		move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
	else:
		if 'lip_syncer' in state_manager.get_item('frame_processors'):
			source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
			if source_audio_path and replace_audio(state_manager.get_item('target_path'), source_audio_path, state_manager.get_item('output_path')):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					process_manager.end()
					return 4
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
		else:
			if restore_audio(state_manager.get_item('target_path'), state_manager.get_item('output_path'), state_manager.get_item('output_video_fps')):
				logger.debug(wording.get('restoring_audio_succeed'), __name__.upper())
			else:
				if is_process_stopping():
					process_manager.end()
					return 4
				logger.warn(wording.get('restoring_audio_skipped'), __name__.upper())
				move_temp_file(state_manager.get_item('target_path'), state_manager.get_item('output_path'))
	# clear temp
	logger.debug(wording.get('clearing_temp'), __name__.upper())
	clear_temp_directory(state_manager.get_item('target_path'))
	# validate video
	if is_video(state_manager.get_item('output_path')):
		seconds = '{:.2f}'.format((time() - start_time))
		logger.info(wording.get('processing_video_succeed').format(seconds = seconds), __name__.upper())
		conditional_log_statistics()
	else:
		logger.error(wording.get('processing_video_failed'), __name__.upper())
		process_manager.end()
		return 1
	process_manager.end()
	return 0


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__.upper())
	return process_manager.is_pending()
