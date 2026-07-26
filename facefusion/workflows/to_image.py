from facefusion import content_analyser, ffmpeg, logger, process_manager, state_manager, translator
from facefusion.filesystem import is_image
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import get_temp_file_path
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, pack_resolution, read_static_image, restrict_image_resolution, scale_resolution, write_image
from facefusion.workflows.core import conditional_get_target_vision_frames, is_process_stopping, process_temp_frame


def analyse_image() -> ErrorCode:
	if content_analyser.analyse_image(state_manager.get_item('target_path')):
		return 3
	return 0


def prepare_image() -> ErrorCode:
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))
	temp_image_resolution = restrict_image_resolution(state_manager.get_item('target_path'), output_image_resolution)

	logger.info(translator.get('copying_image').format(resolution = pack_resolution(temp_image_resolution)), __name__)
	if ffmpeg.copy_image(state_manager.get_item('target_path'), temp_image_resolution):
		logger.debug(translator.get('copying_image_succeeded'), __name__)
	else:
		logger.error(translator.get('copying_image_failed'), __name__)
		process_manager.end()
		return 1
	return 0


def process_image() -> ErrorCode:
	temp_image_path = get_temp_file_path(state_manager.get_item('target_path'))
	target_vision_frames = conditional_get_target_vision_frames(0)
	temp_vision_frame = read_static_image(temp_image_path, 'rgba')
	temp_vision_frame = process_temp_frame(target_vision_frames, temp_vision_frame, 0)
	write_image(temp_image_path, temp_vision_frame)

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		processor_module.post_process()

	if is_process_stopping():
		return 4
	return 0


def finalize_image(start_time : float) -> ErrorCode:
	output_image_resolution = scale_resolution(detect_image_resolution(state_manager.get_item('target_path')), state_manager.get_item('output_image_scale'))

	logger.info(translator.get('finalizing_image').format(resolution = pack_resolution(output_image_resolution)), __name__)
	if ffmpeg.finalize_image(state_manager.get_item('target_path'), state_manager.get_item('output_path'), output_image_resolution):
		logger.debug(translator.get('finalizing_image_succeeded'), __name__)
	else:
		logger.warn(translator.get('finalizing_image_skipped'), __name__)

	if is_image(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_image_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_image_failed'), __name__)
		return 1
	return 0
