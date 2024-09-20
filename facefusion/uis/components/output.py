import tempfile
from typing import Optional

import gradio

from facefusion import state_manager, wording
from facefusion.uis.core import register_ui_component

OUTPUT_PATH_TEXTBOX : Optional[gradio.Textbox] = None
OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None


def render() -> None:
	global OUTPUT_PATH_TEXTBOX
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO

	if not state_manager.get_item('output_path'):
		state_manager.set_item('output_path', tempfile.gettempdir())
	OUTPUT_PATH_TEXTBOX = gradio.Textbox(
		label = wording.get('uis.output_path_textbox'),
		value = state_manager.get_item('output_path'),
		max_lines = 1
	)
	OUTPUT_IMAGE = gradio.Image(
		label = wording.get('uis.output_image_or_video'),
		visible = False
	)
	OUTPUT_VIDEO = gradio.Video(
		label = wording.get('uis.output_image_or_video')
	)


def listen() -> None:
	OUTPUT_PATH_TEXTBOX.change(update_output_path, inputs = OUTPUT_PATH_TEXTBOX)
	register_ui_component('output_image', OUTPUT_IMAGE)
	register_ui_component('output_video', OUTPUT_VIDEO)


def update_output_path(output_path : str) -> None:
	state_manager.set_item('output_path', output_path)
