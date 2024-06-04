import sys
from time import sleep

from facefusion.typing import ErrorCode
from facefusion import process_manager
from facefusion.filesystem import clear_temp
import facefusion.globals


def hard_exit(error_code : ErrorCode) -> None:
	sys.exit(error_code)


def conditional_exit(error_code : ErrorCode) -> None:
	if facefusion.globals.headless:
		hard_exit(error_code)


def graceful_exit(error_code : ErrorCode) -> None:
	process_manager.stop()
	while process_manager.is_processing():
		sleep(0.5)
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	hard_exit(error_code)
