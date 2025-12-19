from functools import partial

from facefusion import process_manager
from facefusion.types import ErrorCode
from facefusion.workflows.core import analyse_image, clear, setup
from facefusion.workflows.to_image import finalize_image, prepare_image, process_image


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
