from typing import Optional
import gradio

import facefusion.choices
import facefusion.globals
from facefusion import wording
from facefusion.typing import OutputVideoEncoder
from facefusion.uis.typing import Update

OUTPUT_VIDEO_ENCODER_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_QUALITY_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global OUTPUT_VIDEO_ENCODER_DROPDOWN
	global OUTPUT_VIDEO_QUALITY_SLIDER

	with gradio.Box():
		OUTPUT_VIDEO_ENCODER_DROPDOWN = gradio.Dropdown(
			label = wording.get('output_video_encoder_dropdown_label'),
			choices = facefusion.choices.output_video_encoder,
			value = facefusion.globals.output_video_encoder
		)
		OUTPUT_VIDEO_QUALITY_SLIDER = gradio.Slider(
			label = wording.get('output_video_quality_slider_label'),
			value = facefusion.globals.output_video_quality,
			step = 1
		)


def listen() -> None:
	OUTPUT_VIDEO_ENCODER_DROPDOWN.select(update_output_video_encoder, inputs = OUTPUT_VIDEO_ENCODER_DROPDOWN, outputs = OUTPUT_VIDEO_ENCODER_DROPDOWN)
	OUTPUT_VIDEO_QUALITY_SLIDER.change(update_output_video_quality, inputs = OUTPUT_VIDEO_QUALITY_SLIDER, outputs = OUTPUT_VIDEO_QUALITY_SLIDER)


def update_output_video_encoder(output_video_encoder: OutputVideoEncoder) -> Update:
	facefusion.globals.output_video_encoder = output_video_encoder
	return gradio.update(value = output_video_encoder)


def update_output_video_quality(output_video_quality : int) -> Update:
	facefusion.globals.output_video_quality = output_video_quality
	return gradio.update(value = output_video_quality)
