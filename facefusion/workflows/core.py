from facefusion import logger, process_manager, wording
from facefusion.temp_helper import clear_temp_directory, create_temp_directory


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__)
	return process_manager.is_pending()


def prepare_temp_directory(target_path : str) -> None:
	logger.debug(wording.get('clearing_temp'), __name__)
	clear_temp_directory(target_path)
	logger.debug(wording.get('creating_temp'), __name__)
	create_temp_directory(target_path)
