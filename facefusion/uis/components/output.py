from typing import Tuple, Optional
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.core import conditional_process
from facefusion.uis.typing import Update
from facefusion.utilities import is_image, is_video, normalize_output_path, clear_temp

OUTPUT_START_BUTTON : Optional[gradio.Button] = None
OUTPUT_CLEAR_BUTTON : Optional[gradio.Button] = None
OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None


def render() -> None:
	global OUTPUT_START_BUTTON
	global OUTPUT_CLEAR_BUTTON
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO

	with gradio.Row():
		with gradio.Box():
			OUTPUT_IMAGE = gradio.Image(
				label = wording.get('output_image_or_video_label'),
				visible = False
			)
			OUTPUT_VIDEO = gradio.Video(
				label = wording.get('output_image_or_video_label')
			)
	with gradio.Row():
		OUTPUT_START_BUTTON = gradio.Button(wording.get('start_button_label'))
		OUTPUT_CLEAR_BUTTON = gradio.Button(wording.get('clear_button_label'))


def listen() -> None:
	OUTPUT_START_BUTTON.click(update, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO ])
	OUTPUT_CLEAR_BUTTON.click(clear, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO ])


def update() -> Tuple[Update, Update]:
	facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, '.')
	if facefusion.globals.output_path:
		conditional_process()
		if is_image(facefusion.globals.output_path):
			return gradio.update(value = facefusion.globals.output_path, visible = True), gradio.update(value = None, visible = False)
		if is_video(facefusion.globals.output_path):
			return gradio.update(value = None, visible = False), gradio.update(value = facefusion.globals.output_path, visible = True)
	return gradio.update(value = None, visible = False), gradio.update(value = None, visible = False)


def clear() -> Tuple[Update, Update]:
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.update(value = None), gradio.update(value = None)
