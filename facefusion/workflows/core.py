from facefusion import logger, process_manager, wording


def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(wording.get('processing_stopped'), __name__)
	return process_manager.is_pending()
