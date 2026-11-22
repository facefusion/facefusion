from functools import partial
from typing import Optional

from facefusion import state_manager
from facefusion.filesystem import has_audio, has_image
from facefusion.types import ErrorCode, WorkflowMode
from facefusion.workflows.core import clear, setup
from facefusion.workflows.to_image import analyse_image, finalize_image, prepare_image, process_image


def detect() -> Optional[WorkflowMode]:
	target_path = state_manager.get_item('target_path')
	source_paths = state_manager.get_item('source_paths')

	if has_image([ target_path ]) and has_audio(source_paths) is False:
		return 'image-to-image'

	return None


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
