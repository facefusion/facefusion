from typing import Any, Dict, Tuple, Optional
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.uis.core import register_ui_component

FACE_MASK_BLUR_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PAD_TOP_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PAD_BOTTOM_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PAD_LEFT_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PAD_RIGHT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_MASK_BLUR_SLIDER
	global FACE_MASK_PAD_TOP_SLIDER
	global FACE_MASK_PAD_BOTTOM_SLIDER
	global FACE_MASK_PAD_LEFT_SLIDER
	global FACE_MASK_PAD_RIGHT_SLIDER

	face_mask_blur_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('face_mask_blur_slider_label'),
		'step': 0.01,
		'minimum': 0,
		'maximum': 1,
		'value': facefusion.globals.face_mask_blur,
		'interactive': True
	}
	face_mask_pad_top_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('face_mask_pad_top_slider_label'),
		'step': 0.01,
		'minimum': 0,
		'maximum': 1,
		'value': facefusion.globals.face_mask_padding[0],
		'interactive': True
	}
	face_mask_pad_bottom_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('face_mask_pad_bottom_slider_label'),
		'step': 0.01,
		'minimum': 0,
		'maximum': 1,
		'value': facefusion.globals.face_mask_padding[1],
		'interactive': True
	}
	face_mask_pad_left_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('face_mask_pad_left_slider_label'),
		'step': 0.01,
		'minimum': 0,
		'maximum': 1,
		'value': facefusion.globals.face_mask_padding[2],
		'interactive': True
	}
	face_mask_pad_right_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('face_mask_pad_right_slider_label'),
		'step': 0.01,
		'minimum': 0,
		'maximum': 1,
		'value': facefusion.globals.face_mask_padding[3],
		'interactive': True
	}
	with gradio.Group():
		FACE_MASK_BLUR_SLIDER = gradio.Slider(**face_mask_blur_slider_args)
		with gradio.Row():
			FACE_MASK_PAD_TOP_SLIDER = gradio.Slider(**face_mask_pad_top_slider_args)
			FACE_MASK_PAD_BOTTOM_SLIDER = gradio.Slider(**face_mask_pad_bottom_slider_args)
		with gradio.Row():
			FACE_MASK_PAD_LEFT_SLIDER = gradio.Slider(**face_mask_pad_left_slider_args)
			FACE_MASK_PAD_RIGHT_SLIDER = gradio.Slider(**face_mask_pad_right_slider_args)
	register_ui_component('face_mask_blur_slider', FACE_MASK_BLUR_SLIDER)
	register_ui_component('face_mask_pad_top_slider', FACE_MASK_PAD_TOP_SLIDER)
	register_ui_component('face_mask_pad_bottom_slider', FACE_MASK_PAD_BOTTOM_SLIDER)
	register_ui_component('face_mask_pad_left_slider', FACE_MASK_PAD_LEFT_SLIDER)
	register_ui_component('face_mask_pad_right_slider', FACE_MASK_PAD_RIGHT_SLIDER)


def listen() -> None:
	FACE_MASK_BLUR_SLIDER.change(update_face_mask_blur, inputs = FACE_MASK_BLUR_SLIDER)
	face_mask_padding_sliders = [FACE_MASK_PAD_TOP_SLIDER, FACE_MASK_PAD_BOTTOM_SLIDER, FACE_MASK_PAD_LEFT_SLIDER, FACE_MASK_PAD_RIGHT_SLIDER]
	for pad_slider in face_mask_padding_sliders:
		pad_slider.change(update_face_mask_padding, inputs = face_mask_padding_sliders)


def update_face_mask_blur(face_mask_blur : float) -> None:
	facefusion.globals.face_mask_blur = face_mask_blur


def update_face_mask_padding(face_mask_padding_top : float, face_mask_padding_bottom : float, face_mask_padding_left : float, face_mask_padding_right : float) -> None:
	facefusion.globals.face_mask_padding = (face_mask_padding_top, face_mask_padding_bottom, face_mask_padding_left, face_mask_padding_right)
