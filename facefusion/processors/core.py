import importlib
from types import ModuleType
from typing import Any, List

from facefusion import logger, wording
from facefusion.exit_helper import hard_exit

PROCESSORS_METHODS =\
[
	'get_inference_pool',
	'clear_inference_pool',
	'register_args',
	'apply_args',
	'pre_check',
	'pre_process',
	'post_process',
	'process_frame'
]


def load_processor_module(processor : str) -> Any:
	try:
		processor_module = importlib.import_module('facefusion.processors.modules.' + processor)
		for method_name in PROCESSORS_METHODS:
			if not hasattr(processor_module, method_name):
				raise NotImplementedError
	except ModuleNotFoundError as exception:
		logger.error(wording.get('processor_not_loaded').format(processor = processor), __name__)
		logger.debug(exception.msg, __name__)
		hard_exit(1)
	except NotImplementedError:
		logger.error(wording.get('processor_not_implemented').format(processor = processor), __name__)
		hard_exit(1)
	return processor_module


def get_processors_modules(processors : List[str]) -> List[ModuleType]:
	processor_modules = []

	for processor in processors:
		processor_module = load_processor_module(processor)
		processor_modules.append(processor_module)
	return processor_modules
