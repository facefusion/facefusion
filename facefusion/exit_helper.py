import sys
from time import sleep

from facefusion.typing import ErrorCode
from facefusion.state_manager import get_state_item
from facefusion import process_manager
from facefusion.temp_helper import clear_temp_directory


def hard_exit(error_code : ErrorCode) -> None:
	sys.exit(error_code)


def conditional_exit(error_code : ErrorCode) -> None:
	if get_state_item('headless'):
		hard_exit(error_code)


def graceful_exit(error_code : ErrorCode) -> None:
	process_manager.stop()
	while process_manager.is_processing():
		sleep(0.5)
	if get_state_item('target_path'):
		clear_temp_directory(get_state_item('target_path'))
	hard_exit(error_code)
