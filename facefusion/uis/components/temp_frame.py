from typing import Optional

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.filesystem import is_video
from facefusion.types import TempFrameFormat
from facefusion.uis.core import get_ui_component

TEMP_FRAME_FORMAT_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global TEMP_FRAME_FORMAT_DROPDOWN

	TEMP_FRAME_FORMAT_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.temp_frame_format_dropdown'),
		choices = facefusion.choices.temp_frame_formats,
		value = state_manager.get_item('temp_frame_format'),
		visible = is_video(state_manager.get_item('target_path'))
	)


def listen() -> None:
	TEMP_FRAME_FORMAT_DROPDOWN.change(update_temp_frame_format, inputs = TEMP_FRAME_FORMAT_DROPDOWN)

	target_video = get_ui_component('target_video')
	if target_video:
		for method in [ 'change', 'clear' ]:
			getattr(target_video, method)(remote_update, outputs = TEMP_FRAME_FORMAT_DROPDOWN)


def remote_update() -> gradio.Dropdown:
	if is_video(state_manager.get_item('target_path')):
		return gradio.Dropdown(visible = True)
	return gradio.Dropdown(visible = False)


def update_temp_frame_format(temp_frame_format : TempFrameFormat) -> None:
	state_manager.set_item('temp_frame_format', temp_frame_format)

