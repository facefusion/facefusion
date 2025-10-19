import tempfile
from pathlib import Path
from typing import Optional

import gradio

from facefusion import state_manager, translator
from facefusion.uis.core import register_ui_component
from facefusion.locals import LOCALS


translator.load(LOCALS, __name__)

OUTPUT_PATH_TEXTBOX : Optional[gradio.Textbox] = None
OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None


def render() -> None:
	global OUTPUT_PATH_TEXTBOX
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO

	if not state_manager.get_item('output_path'):
		documents_directory = Path.home().joinpath('Documents')

		if documents_directory.exists():
			state_manager.set_item('output_path', documents_directory)
		else:
			state_manager.set_item('output_path', tempfile.gettempdir())
	OUTPUT_PATH_TEXTBOX = gradio.Textbox(
		label = translator.get('uis.output_path_textbox', __name__),
		value = state_manager.get_item('output_path'),
		max_lines = 1
	)
	OUTPUT_IMAGE = gradio.Image(
		label = translator.get('uis.output_image_or_video', __name__),
		visible = False
	)
	OUTPUT_VIDEO = gradio.Video(
		label = translator.get('uis.output_image_or_video', __name__)
	)


def listen() -> None:
	OUTPUT_PATH_TEXTBOX.change(update_output_path, inputs = OUTPUT_PATH_TEXTBOX)
	register_ui_component('output_image', OUTPUT_IMAGE)
	register_ui_component('output_video', OUTPUT_VIDEO)


def update_output_path(output_path : str) -> None:
	state_manager.set_item('output_path', output_path)
