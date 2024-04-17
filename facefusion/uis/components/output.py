from typing import Tuple, Optional
from time import sleep
import gradio

import facefusion.globals
from facefusion import process_manager, wording
from facefusion.core import conditional_process
from facefusion.memory import limit_system_memory
from facefusion.normalizer import normalize_output_path
from facefusion.uis.core import get_ui_component
from facefusion.filesystem import clear_temp, is_image, is_video
from facefusion.uis.typing import Update

OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None
OUTPUT_START_BUTTON : Optional[gradio.Button] = None
OUTPUT_CLEAR_BUTTON : Optional[gradio.Button] = None
OUTPUT_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO
	global OUTPUT_START_BUTTON
	global OUTPUT_STOP_BUTTON
	global OUTPUT_CLEAR_BUTTON

	OUTPUT_IMAGE = gradio.Image(
		label = wording.get('uis.output_image_or_video'),
		visible = False
	)
	OUTPUT_VIDEO = gradio.Video(
		label = wording.get('uis.output_image_or_video')
	)
	OUTPUT_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	OUTPUT_STOP_BUTTON = gradio.Button(
		value = wording.get('uis.stop_button'),
		variant = 'primary',
		size = 'sm',
		visible = False
	)
	OUTPUT_CLEAR_BUTTON = gradio.Button(
		value = wording.get('uis.clear_button'),
		size = 'sm'
	)


def listen() -> None:
	output_path_textbox = get_ui_component('output_path_textbox')
	if output_path_textbox:
		OUTPUT_START_BUTTON.click(start, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
		OUTPUT_START_BUTTON.click(process, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO, OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_STOP_BUTTON.click(stop, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_CLEAR_BUTTON.click(clear, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO ])


def start() -> Tuple[Update, Update]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.update(visible = False), gradio.update(visible = True)


def process() -> Tuple[Update, Update, Update, Update]:
	normed_output_path = normalize_output_path(facefusion.globals.target_path, facefusion.globals.output_path)
	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	conditional_process()
	if is_image(normed_output_path):
		return gradio.update(value = normed_output_path, visible = True), gradio.update(value = None, visible = False), gradio.update(visible = True), gradio.update(visible = False)
	if is_video(normed_output_path):
		return gradio.update(value = None, visible = False), gradio.update(value = normed_output_path, visible = True), gradio.update(visible = True), gradio.update(visible = False)
	return gradio.update(value = None), gradio.update(value = None), gradio.update(visible = True), gradio.update(visible = False)


def stop() -> Tuple[Update, Update]:
	process_manager.stop()
	return gradio.update(visible = True), gradio.update(visible = False)


def clear() -> Tuple[Update, Update]:
	while process_manager.is_processing():
		sleep(0.5)
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.update(value = None), gradio.update(value = None)
