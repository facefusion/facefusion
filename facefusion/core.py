import inspect
import itertools
import shutil
import signal
import sys
from time import time

import uvicorn

from facefusion import args_store, benchmarker, cli_helper, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, hash_helper, logger, state_manager, translator, voice_extractor
from facefusion.apis.core import create_api
from facefusion.args_helper import apply_args
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.exit_helper import hard_exit, signal_exit
from facefusion.filesystem import get_file_extension, has_audio, has_image, has_video
from facefusion.filesystem import get_file_name, resolve_file_paths, resolve_file_pattern
from facefusion.jobs import job_helper, job_manager, job_runner
from facefusion.jobs.job_list import compose_job_list
from facefusion.processors.core import get_processors_modules
from facefusion.program import create_program
from facefusion.program_helper import validate_args
from facefusion.types import Args, ErrorCode, WorkFlow
from facefusion.workflows import audio_to_image, image_to_image, image_to_video, image_to_video_as_frames


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
	if state_manager.get_item('command') == 'force-download':
		error_code = force_download()
		hard_exit(error_code)

	if state_manager.get_item('command') == 'benchmark':
		if not common_pre_check() or not processors_pre_check() or not benchmarker.pre_check():
			hard_exit(2)
		benchmarker.render()

	if state_manager.get_item('command') == 'api':
		logger.info(translator.get('api_started').format(host = state_manager.get_item('api_host'), port = state_manager.get_item('api_port')), __name__)
		uvicorn.run(create_api(), host = state_manager.get_item('api_host'), port = state_manager.get_item('api_port'))
		hard_exit(1)

	if state_manager.get_item('command') in [ 'job-list', 'job-create', 'job-submit', 'job-submit-all', 'job-delete', 'job-delete-all', 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]:
		if not job_manager.init_jobs(state_manager.get_jobs_path()):
			hard_exit(1)
		error_code = route_job_manager(args)
		hard_exit(error_code)

	if state_manager.get_item('command') == 'run':
		if not job_manager.init_jobs(state_manager.get_jobs_path()):
			hard_exit(1)
		error_code = process_headless(args)
		hard_exit(error_code)

	if state_manager.get_item('command') == 'batch-run':
		if not job_manager.init_jobs(state_manager.get_jobs_path()):
			hard_exit(1)
		error_code = process_batch(args)
		hard_exit(error_code)

	if state_manager.get_item('command') in [ 'job-run', 'job-run-all', 'job-retry', 'job-retry-all' ]:
		if not job_manager.init_jobs(state_manager.get_jobs_path()):
			hard_exit(1)
		error_code = route_job_runner()
		hard_exit(error_code)


def pre_check() -> bool:
	if sys.version_info < (3, 10):
		logger.error(translator.get('python_not_supported').format(version = '3.10'), __name__)
		return False

	if not shutil.which('curl'):
		logger.error(translator.get('curl_not_installed'), __name__)
		return False

	if not shutil.which('ffmpeg'):
		logger.error(translator.get('ffmpeg_not_installed'), __name__)
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

	return all(module.pre_check() for module in common_modules) and content_analyser_hash == 'b14e7b92'


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
			logger.info(translator.get('job_created').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(translator.get('job_not_created').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-submit':
		if job_manager.submit_job(state_manager.get_item('job_id')):
			logger.info(translator.get('job_submitted').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(translator.get('job_not_submitted').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-submit-all':
		if job_manager.submit_jobs(state_manager.get_item('halt_on_error')):
			logger.info(translator.get('job_all_submitted'), __name__)
			return 0
		logger.error(translator.get('job_all_not_submitted'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-delete':
		if job_manager.delete_job(state_manager.get_item('job_id')):
			logger.info(translator.get('job_deleted').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(translator.get('job_not_deleted').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-delete-all':
		if job_manager.delete_jobs(state_manager.get_item('halt_on_error')):
			logger.info(translator.get('job_all_deleted'), __name__)
			return 0
		logger.error(translator.get('job_all_not_deleted'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-add-step':
		step_args = args_store.filter_step_args(args)

		if job_manager.add_step(state_manager.get_item('job_id'), step_args):
			logger.info(translator.get('job_step_added').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.error(translator.get('job_step_not_added').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-remix-step':
		step_args = args_store.filter_step_args(args)

		if job_manager.remix_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(translator.get('job_remix_step_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(translator.get('job_remix_step_not_added').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-insert-step':
		step_args = args_store.filter_step_args(args)

		if job_manager.insert_step(state_manager.get_item('job_id'), state_manager.get_item('step_index'), step_args):
			logger.info(translator.get('job_step_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(translator.get('job_step_not_inserted').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-remove-step':
		if job_manager.remove_step(state_manager.get_item('job_id'), state_manager.get_item('step_index')):
			logger.info(translator.get('job_step_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
			return 0
		logger.error(translator.get('job_step_not_removed').format(job_id = state_manager.get_item('job_id'), step_index = state_manager.get_item('step_index')), __name__)
		return 1
	return 1


def route_job_runner() -> ErrorCode:
	if state_manager.get_item('command') == 'job-run':
		logger.info(translator.get('running_job').format(job_id = state_manager.get_item('job_id')), __name__)
		if job_runner.run_job(state_manager.get_item('job_id'), process_step):
			logger.info(translator.get('processing_job_succeeded').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.info(translator.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-run-all':
		logger.info(translator.get('running_jobs'), __name__)
		if job_runner.run_jobs(process_step, state_manager.get_item('halt_on_error')):
			logger.info(translator.get('processing_jobs_succeeded'), __name__)
			return 0
		logger.info(translator.get('processing_jobs_failed'), __name__)
		return 1

	if state_manager.get_item('command') == 'job-retry':
		logger.info(translator.get('retrying_job').format(job_id = state_manager.get_item('job_id')), __name__)
		if job_runner.retry_job(state_manager.get_item('job_id'), process_step):
			logger.info(translator.get('processing_job_succeeded').format(job_id = state_manager.get_item('job_id')), __name__)
			return 0
		logger.info(translator.get('processing_job_failed').format(job_id = state_manager.get_item('job_id')), __name__)
		return 1

	if state_manager.get_item('command') == 'job-retry-all':
		logger.info(translator.get('retrying_jobs'), __name__)
		if job_runner.retry_jobs(process_step, state_manager.get_item('halt_on_error')):
			logger.info(translator.get('processing_jobs_succeeded'), __name__)
			return 0
		logger.info(translator.get('processing_jobs_failed'), __name__)
		return 1
	return 2


def process_headless(args : Args) -> ErrorCode:
	job_id = job_helper.suggest_job_id('headless')
	step_args = args_store.filter_step_args(args)

	if job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
		return 0
	return 1


def process_batch(args : Args) -> ErrorCode:
	job_id = job_helper.suggest_job_id('batch')
	step_args = args_store.filter_step_args(args)
	source_paths = resolve_file_pattern(step_args.get('source_pattern'))
	target_paths = resolve_file_pattern(step_args.get('target_pattern'))

	if job_manager.create_job(job_id):
		if source_paths and target_paths:
			for index, (source_path, target_path) in enumerate(itertools.product(source_paths, target_paths)):
				step_args['source_paths'] = [ source_path ]
				step_args['target_path'] = target_path

				try:
					step_args['output_path'] = step_args.get('output_pattern').format(index = index, source_name = get_file_name(source_path), target_name = get_file_name(target_path), target_extension = get_file_extension(target_path))
				except KeyError:
					return 1

				if not job_manager.add_step(job_id, step_args):
					return 1
			if job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
				return 0

		if not source_paths and target_paths:
			for index, target_path in enumerate(target_paths):
				step_args['target_path'] = target_path

				try:
					step_args['output_path'] = step_args.get('output_pattern').format(index = index, target_name = get_file_name(target_path), target_extension = get_file_extension(target_path))
				except KeyError:
					return 1

				if not job_manager.add_step(job_id, step_args):
					return 1
			if job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step):
				return 0
	return 1


def process_step(job_id : str, step_index : int, step_args : Args) -> bool:
	step_total = job_manager.count_step_total(job_id)
	cli_args = args_store.filter_cli_args(state_manager.get_state()) #type:ignore[arg-type]
	args = cli_args.copy()
	args.update(step_args)
	apply_args(args, state_manager.set_item)

	logger.info(translator.get('processing_step').format(step_current = step_index + 1, step_total = step_total), __name__)
	if common_pre_check() and processors_pre_check():
		error_code = conditional_process()
		return error_code == 0
	return False


def conditional_process() -> ErrorCode:
	start_time = time()

	if state_manager.get_item('workflow') == 'auto':
		state_manager.set_item('workflow', detect_workflow())

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		if not processor_module.pre_process('output'):
			return 2

	if state_manager.get_item('workflow') == 'audio-to-image:video':
		return audio_to_image.process(start_time)
	if state_manager.get_item('workflow') == 'image-to-image':
		return image_to_image.process(start_time)
	if state_manager.get_item('workflow') == 'image-to-video':
		return image_to_video.process(start_time)
	if state_manager.get_item('workflow') == 'image-to-video:frames':
		return image_to_video_as_frames.process(start_time)

	return 0


def detect_workflow() -> WorkFlow:
	if has_video([ state_manager.get_item('target_path') ]):
		if get_file_extension(state_manager.get_item('output_path')):
			return 'image-to-video'
		return 'image-to-video:frames'

	if has_audio(state_manager.get_item('source_paths')) and has_image([ state_manager.get_item('target_path') ]):
		return 'audio-to-image:video'

	return 'image-to-image'
