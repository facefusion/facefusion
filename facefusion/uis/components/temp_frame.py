from typing import Optional
import gradio

import facefusion.choices
import facefusion.globals
from facefusion import wording
from facefusion.typing import TempFrameFormat

from facefusion.uis.typing import Update

TEMP_FRAME_FORMAT_DROPDOWN : Optional[gradio.Dropdown] = None
TEMP_FRAME_QUALITY_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global TEMP_FRAME_FORMAT_DROPDOWN
	global TEMP_FRAME_QUALITY_SLIDER

	with gradio.Box():
		TEMP_FRAME_FORMAT_DROPDOWN = gradio.Dropdown(
			label = wording.get('temp_frame_format_dropdown_label'),
			choices = facefusion.choices.temp_frame_format,
			value = facefusion.globals.temp_frame_format
		)
		TEMP_FRAME_QUALITY_SLIDER = gradio.Slider(
			label = wording.get('temp_frame_quality_slider_label'),
			value = facefusion.globals.temp_frame_quality,
			step = 1
		)


def listen() -> None:
	TEMP_FRAME_FORMAT_DROPDOWN.select(update_temp_frame_format, inputs = TEMP_FRAME_FORMAT_DROPDOWN, outputs = TEMP_FRAME_FORMAT_DROPDOWN)
	TEMP_FRAME_QUALITY_SLIDER.change(update_temp_frame_quality, inputs = TEMP_FRAME_QUALITY_SLIDER, outputs = TEMP_FRAME_QUALITY_SLIDER)


def update_temp_frame_format(temp_frame_format : TempFrameFormat) -> Update:
	facefusion.globals.temp_frame_format = temp_frame_format
	return gradio.update(value = temp_frame_format)


def update_temp_frame_quality(temp_frame_quality : int) -> Update:
	facefusion.globals.temp_frame_quality = temp_frame_quality
	return gradio.update(value = temp_frame_quality)
