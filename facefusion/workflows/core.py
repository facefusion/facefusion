from facefusion import logger, process_manager, translator
from facefusion.locals import LOCALS



translator.load(LOCALS, __name__)

def is_process_stopping() -> bool:
	if process_manager.is_stopping():
		process_manager.end()
		logger.info(translator.get('processing_stopped', __name__), __name__)
	return process_manager.is_pending()
