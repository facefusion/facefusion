import io
import logging
import math
import os
from typing import Optional

import gradio
from tqdm import tqdm

import facefusion.choices
from facefusion import logger, state_manager, wording
from facefusion.types import LogLevel

LOG_LEVEL_DROPDOWN : Optional[gradio.Dropdown] = None
TERMINAL_TEXTBOX : Optional[gradio.Textbox] = None
LOG_BUFFER = io.StringIO()
LOG_HANDLER = logging.StreamHandler(LOG_BUFFER)
TQDM_UPDATE = tqdm.update


def render() -> None:
	global LOG_LEVEL_DROPDOWN
	global TERMINAL_TEXTBOX

	LOG_LEVEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.log_level_dropdown'),
		choices = facefusion.choices.log_levels,
		value = state_manager.get_item('log_level')
	)
	TERMINAL_TEXTBOX = gradio.Textbox(
		label = wording.get('uis.terminal_textbox'),
		value = read_logs,
		lines = 8,
		max_lines = 8,
		every = 0.5,
		show_copy_button = True
	)


def listen() -> None:
	LOG_LEVEL_DROPDOWN.change(update_log_level, inputs = LOG_LEVEL_DROPDOWN)
	logger.get_package_logger().addHandler(LOG_HANDLER)
	tqdm.update = tqdm_update


def update_log_level(log_level : LogLevel) -> None:
	state_manager.set_item('log_level', log_level)
	logger.init(state_manager.get_item('log_level'))


def tqdm_update(self : tqdm, n : int = 1) -> None:
	TQDM_UPDATE(self, n)
	output = create_tqdm_output(self)

	if output:
		LOG_BUFFER.seek(0)
		log_buffer = LOG_BUFFER.read()
		lines = log_buffer.splitlines()
		if lines and lines[-1].startswith(self.desc):
			position = log_buffer.rfind(lines[-1])
			LOG_BUFFER.seek(position)
		else:
			LOG_BUFFER.seek(0, os.SEEK_END)
		LOG_BUFFER.write(output + os.linesep)
		LOG_BUFFER.flush()


def create_tqdm_output(self : tqdm) -> Optional[str]:
	if not self.disable and self.desc and self.total:
		percentage = math.floor(self.n / self.total * 100)
		return self.desc + wording.get('colon') + ' ' + str(percentage) + '% (' + str(self.n) + '/' + str(self.total) + ')'
	if not self.disable and self.desc and self.unit:
		return self.desc + wording.get('colon') + ' ' + str(self.n) + ' ' + self.unit
	return None


def read_logs() -> str:
	LOG_BUFFER.seek(0)
	logs = LOG_BUFFER.read().strip()
	return logs
