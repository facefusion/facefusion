from facefusion import logger, process_manager, state_manager, wording
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_image
from facefusion.ffmpeg import copy_image, finalize_image
from facefusion.filesystem import is_image
from facefusion.processors.core import get_processors_modules
from facefusion.temp_helper import clear_temp_directory, get_temp_file_path
from facefusion.time_helper import calculate_end_time
from facefusion.types import ErrorCode
from facefusion.vision import detect_image_resolution, pack_resolution, read_static_image, read_static_images, restrict_image_resolution, scale_resolution, write_image
from facefusion.workflows.core import is_process_stopping, prepare_temp_directory


def process_image(start_time : float) -> ErrorCode:
	if analyse_image(state_manager.get_item('target_path')):
		return 3

	prepare_temp_directory(state_manager.get_item('target_path'))
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
