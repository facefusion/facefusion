import io
import logging
import gradio as gr
from typing import Optional

from facefusion import logger, wording

TERMINAL_TEXTBOX: Optional[gr.Textbox] = None
LOG_BUFFER = io.StringIO()
LOG_HANDLER = logging.StreamHandler(LOG_BUFFER)


def render() -> None:
	global TERMINAL_TEXTBOX

	TERMINAL_TEXTBOX = gr.Textbox(
		label = wording.get('uis.terminal_textbox'),
		value = read_logs,
		lines = 5,
		every = 0.5
	)


def listen() -> None:
	logger.get_package_logger().addHandler(LOG_HANDLER)


def read_logs() -> str:
	LOG_BUFFER.seek(0)
	logs = LOG_BUFFER.read()
	return logs
