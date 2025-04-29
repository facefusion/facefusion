from typing import Optional

import gradio

import facefusion.choices
from facefusion import wording
from facefusion.common_helper import get_first
from facefusion.uis.components.webcam import get_available_webcam_ids
from facefusion.uis.core import register_ui_component

WEBCAM_DEVICE_ID_DROPDOWN : Optional[gradio.Dropdown] = None
WEBCAM_MODE_RADIO : Optional[gradio.Radio] = None
WEBCAM_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
WEBCAM_FPS_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global WEBCAM_DEVICE_ID_DROPDOWN
	global WEBCAM_MODE_RADIO
	global WEBCAM_RESOLUTION_DROPDOWN
	global WEBCAM_FPS_SLIDER

	available_webcam_ids = get_available_webcam_ids(0, 10) or [ 'none' ] #type:ignore[list-item]
	WEBCAM_DEVICE_ID_DROPDOWN = gradio.Dropdown(
		value = get_first(available_webcam_ids),
		label = wording.get('uis.webcam_device_id_dropdown'),
		choices = available_webcam_ids
	)
	WEBCAM_MODE_RADIO = gradio.Radio(
		label = wording.get('uis.webcam_mode_radio'),
		choices = facefusion.choices.webcam_modes,
		value = 'inline'
	)
	WEBCAM_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.webcam_resolution_dropdown'),
		choices = facefusion.choices.webcam_resolutions,
		value = facefusion.choices.webcam_resolutions[0]
	)
	WEBCAM_FPS_SLIDER = gradio.Slider(
		label = wording.get('uis.webcam_fps_slider'),
		value = 25,
		step = 1,
		minimum = 1,
		maximum = 60
	)
	register_ui_component('webcam_device_id_dropdown', WEBCAM_DEVICE_ID_DROPDOWN)
	register_ui_component('webcam_mode_radio', WEBCAM_MODE_RADIO)
	register_ui_component('webcam_resolution_dropdown', WEBCAM_RESOLUTION_DROPDOWN)
	register_ui_component('webcam_fps_slider', WEBCAM_FPS_SLIDER)
