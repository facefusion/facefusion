from functools import partial

from facefusion import ffmpeg
from facefusion import logger, process_manager, state_manager, translator
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_image
from facefusion.filesystem import is_image
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, create_temp_directory, get_temp_file_path
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import conditional_merge_vision_mask, detect_image_resolution, extract_vision_mask, pack_resolution, read_static_image, read_static_images, restrict_image_resolution, scale_resolution, write_image
from facefusion.workflows.core import is_process_stopping


def process(start_time : float) -> ErrorCode:
	tasks =\
	[
		setup,
		prepare_image,
		process_image,
		partial(finalize_image, start_time),
	]
	process_manager.start()

	for task in tasks:
		error_code = task() # type:ignore[operator]

		if error_code > 0:
			process_manager.end()
			return error_code

	process_manager.end()
	return 0


def setup() -> ErrorCode:
	if analyse_image(state_manager.get_item('target_path')):
		return 3

	logger.debug(translator.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))
	logger.debug(translator.get('creating_temp'), __name__)
	create_temp_directory(state_manager.get_item('target_path'))
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
	reference_vision_frame = read_static_image(temp_image_path)
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	target_vision_frame = read_static_image(temp_image_path, 'rgba')
	temp_vision_frame = target_vision_frame.copy()
	temp_vision_mask = extract_vision_mask(temp_vision_frame)

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.info(translator.get('processing'), processor_module.__name__)

		temp_vision_frame, temp_vision_mask = processor_module.process_frame(
		{
			'reference_vision_frame': reference_vision_frame,
			'source_vision_frames': source_vision_frames,
			'source_audio_frame': source_audio_frame,
			'source_voice_frame': source_voice_frame,
			'target_vision_frame': target_vision_frame[:, :, :3],
			'temp_vision_frame': temp_vision_frame[:, :, :3],
			'temp_vision_mask': temp_vision_mask
		})

		processor_module.post_process()

	temp_vision_frame = conditional_merge_vision_mask(temp_vision_frame, temp_vision_mask)
	write_image(temp_image_path, temp_vision_frame)

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

	logger.debug(translator.get('clearing_temp'), __name__)
	clear_temp_directory(state_manager.get_item('target_path'))

	if is_image(state_manager.get_item('output_path')):
		logger.info(translator.get('processing_image_succeeded').format(seconds = calculate_end_time(start_time)), __name__)
	else:
		logger.error(translator.get('processing_image_failed'), __name__)
		return 1
	return 0
