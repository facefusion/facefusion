from functools import partial

from facefusion.types import ErrorCode
from facefusion.workflows.core import clear, setup
from facefusion.workflows.to_image import analyse_image, finalize_image, prepare_image, process_image


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

	for task in tasks:
		error_code = task() #type:ignore[operator]

		if error_code > 0:
			return error_code

	return 0
