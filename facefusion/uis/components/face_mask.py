from typing import Optional
import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.uis.core import register_ui_component

FACE_MASK_BLUR_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_TOP_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_RIGHT_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_BOTTOM_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_LEFT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_MASK_BLUR_SLIDER
	global FACE_MASK_PADDING_TOP_SLIDER
	global FACE_MASK_PADDING_RIGHT_SLIDER
	global FACE_MASK_PADDING_BOTTOM_SLIDER
	global FACE_MASK_PADDING_LEFT_SLIDER

	FACE_MASK_BLUR_SLIDER = gradio.Slider(
		label = wording.get('face_mask_blur_slider_label'),
		step = facefusion.choices.face_mask_blur_range[1] - facefusion.choices.face_mask_blur_range[0],
		minimum = facefusion.choices.face_mask_blur_range[0],
		maximum = facefusion.choices.face_mask_blur_range[-1],
		value = facefusion.globals.face_mask_blur
	)
	with gradio.Group():
		with gradio.Row():
			FACE_MASK_PADDING_TOP_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_top_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[0]
			)
			FACE_MASK_PADDING_RIGHT_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_right_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[1]
			)
		with gradio.Row():
			FACE_MASK_PADDING_BOTTOM_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_bottom_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[2]
			)
			FACE_MASK_PADDING_LEFT_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_left_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[3]
			)
	register_ui_component('face_mask_blur_slider', FACE_MASK_BLUR_SLIDER)
	register_ui_component('face_mask_padding_top_slider', FACE_MASK_PADDING_TOP_SLIDER)
	register_ui_component('face_mask_padding_right_slider', FACE_MASK_PADDING_RIGHT_SLIDER)
	register_ui_component('face_mask_padding_bottom_slider', FACE_MASK_PADDING_BOTTOM_SLIDER)
	register_ui_component('face_mask_padding_left_slider', FACE_MASK_PADDING_LEFT_SLIDER)


def listen() -> None:
	FACE_MASK_BLUR_SLIDER.change(update_face_mask_blur, inputs = FACE_MASK_BLUR_SLIDER)
	face_mask_padding_sliders = [ FACE_MASK_PADDING_TOP_SLIDER, FACE_MASK_PADDING_RIGHT_SLIDER, FACE_MASK_PADDING_BOTTOM_SLIDER, FACE_MASK_PADDING_LEFT_SLIDER ]
	for face_mask_padding_slider in face_mask_padding_sliders:
		face_mask_padding_slider.change(update_face_mask_padding, inputs = face_mask_padding_sliders)


def update_face_mask_blur(face_mask_blur : float) -> None:
	facefusion.globals.face_mask_blur = face_mask_blur


def update_face_mask_padding(face_mask_padding_top : int, face_mask_padding_right : int, face_mask_padding_bottom : int, face_mask_padding_left : int) -> None:
	facefusion.globals.face_mask_padding = (face_mask_padding_top, face_mask_padding_right, face_mask_padding_bottom, face_mask_padding_left)
