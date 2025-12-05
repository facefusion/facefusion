from functools import partial

from facefusion import content_analyser, ffmpeg, logger, process_manager, state_manager, translator
from facefusion.filesystem import is_image
from facefusion.temp_helper import get_temp_file_path
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, pack_resolution, restrict_image_resolution, scale_resolution
from facefusion.workflows.core import clear, is_process_stopping, process_temp_frame, setup


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		analyse_image,
		clear,
		setup,
		prepare_image,
		process_image,
		partial(finalize_image, start_time),
		clear
	]

	process_manager.start()

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0


def analyse_image() -> ErrorCode:
	if content_analyser.analyse_image(state_manager.get_item('target_path')):
		return 3
	return 0


def prepare_image() -> ErrorCode:
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_image_resolution = restrict_image_resolution(state_manager.get_item('target_path'), output_image_resolution)

	logger.info(translator.get('copying_image').format(resolution = pack_resolution(temp_image_resolution)), __name__)
	if ffmpeg.copy_image(state_manager.get_item('target_path'), state_manager.get_item('output_path'), temp_image_resolution):
		logger.debug(translator.get('copying_image_succeeded'), __name__)
	else:
		logger.error(translator.get('copying_image_failed'), __name__)
		process_manager.end()
		return 1
	return 0


def process_image() -> ErrorCode:
	temp_image_path = get_temp_file_path(state_manager.get_temp_path(), state_manager.get_item('output_path'))
	process_temp_frame(temp_image_path, 0)

	if is_process_stopping():
		return 4
	return 0


def finalize_image(start_time : float) -> ErrorCode:
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))

	logger.info(translator.get('finalizing_image').format(resolution = pack_resolution(output_image_resolution)), __name__)
	if ffmpeg.finalize_image(state_manager.get_item('output_path'), output_image_resolution):
		logger.debug(translator.get('finalizing_image_succeeded'), __name__)
	else:
		logger.warn(translator.get('finalizing_image_skipped'), __name__)

	if is_image(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_image_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_image_failed'), __name__)
		return 1
	return 0
