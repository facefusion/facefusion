import io
import logging
import math
import os
from typing import Optional

import gradio as gr
from tqdm import tqdm

from facefusion import logger, wording

TERMINAL_TEXTBOX: Optional[gr.Textbox] = None
LOG_BUFFER = io.StringIO()
LOG_HANDLER = logging.StreamHandler(LOG_BUFFER)
TQDM_UPDATE = tqdm.update


def render() -> None:
	global TERMINAL_TEXTBOX

	TERMINAL_TEXTBOX = gr.Textbox(
		label = wording.get('uis.terminal_textbox'),
		value = read_logs,
		lines = 8,
		max_lines = 8,
		every = 0.5,
		show_copy_button = True
	)


def listen() -> None:
	logger.get_package_logger().addHandler(LOG_HANDLER)
	tqdm.update = tqdm_update


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
	logs = LOG_BUFFER.read().rstrip()
	return logs
