from facefusion import logger, process_manager, state_manager, translator
from facefusion.temp_helper import clear_temp_directory, create_temp_directory
from facefusion.types import ErrorCode


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped'), __name__)
	return process_manager.is_pending()


def setup() -> ErrorCode:
	create_temp_directory(state_manager.get_item('temp_path'), state_manager.get_item('output_path'))
	logger.debug(translator.get('creating_temp'), __name__)
	return 0


def clear() -> ErrorCode:
	if not state_manager.get_item('keep_temp'):
		clear_temp_directory(state_manager.get_item('temp_path'), state_manager.get_item('output_path'))
		logger.debug(translator.get('clearing_temp'), __name__)
	return 0
