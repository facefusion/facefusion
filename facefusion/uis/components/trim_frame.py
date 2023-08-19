from time import sleep
from typing import Any, Dict, Tuple, Optional

import gradio

import facefusion.globals
from facefusion import wording
from facefusion.capturer import get_video_frame_total
from facefusion.uis import core as ui
from facefusion.uis.typing import Update
from facefusion.utilities import is_video

TRIM_FRAME_START_SLIDER : Optional[gradio.Slider] = None
TRIM_FRAME_END_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global TRIM_FRAME_START_SLIDER
	global TRIM_FRAME_END_SLIDER

	with gradio.Box():
		trim_frame_start_slider_args : Dict[str, Any] = {
			'label': wording.get('trim_frame_start_slider_label'),
			'value': facefusion.globals.trim_frame_start,
			'step': 1,
			'visible': False
		}
		trim_frame_end_slider_args : Dict[str, Any] = {
			'label': wording.get('trim_frame_end_slider_label'),
			'value': facefusion.globals.trim_frame_end,
			'step': 1,
			'visible': False
		}
		if is_video(facefusion.globals.target_path):
			video_frame_total = get_video_frame_total(facefusion.globals.target_path)
			trim_frame_start_slider_args['maximum'] = video_frame_total
			trim_frame_start_slider_args['visible'] = True
			trim_frame_end_slider_args['value'] = video_frame_total
			trim_frame_end_slider_args['maximum'] = video_frame_total
			trim_frame_end_slider_args['visible'] = True
		with gradio.Row():
			TRIM_FRAME_START_SLIDER = gradio.Slider(**trim_frame_start_slider_args)
			TRIM_FRAME_END_SLIDER = gradio.Slider(**trim_frame_end_slider_args)


def listen() -> None:
	target_file = ui.get_component('target_file')
	if target_file:
		target_file.change(remote_update, outputs = [ TRIM_FRAME_START_SLIDER, TRIM_FRAME_END_SLIDER ])
	TRIM_FRAME_START_SLIDER.change(lambda value : update_number('trim_frame_start', int(value)), inputs = TRIM_FRAME_START_SLIDER, outputs = TRIM_FRAME_START_SLIDER)
	TRIM_FRAME_END_SLIDER.change(lambda value : update_number('trim_frame_end', int(value)), inputs = TRIM_FRAME_END_SLIDER, outputs = TRIM_FRAME_END_SLIDER)


def remote_update() -> Tuple[Update, Update]:
	sleep(0.1)
	if is_video(facefusion.globals.target_path):
		video_frame_total = get_video_frame_total(facefusion.globals.target_path)
		facefusion.globals.trim_frame_start = 0
		facefusion.globals.trim_frame_end = video_frame_total
		return gradio.update(value = 0, maximum = video_frame_total, visible = True), gradio.update(value = video_frame_total, maximum = video_frame_total, visible = True)
	return gradio.update(value = None, maximum = None, visible = False), gradio.update(value = None, maximum = None, visible = False)


def update_number(name : str, value : int) -> Update:
	setattr(facefusion.globals, name, value)
	return gradio.update(value = value)
