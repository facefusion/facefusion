from typing import Optional
import gradio

from facefusion import wording
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component

WEBCAM_MODE_RADIO : Optional[gradio.Radio] = None
WEBCAM_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
WEBCAM_FPS_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global WEBCAM_MODE_RADIO
	global WEBCAM_RESOLUTION_DROPDOWN
	global WEBCAM_FPS_SLIDER

	WEBCAM_MODE_RADIO = gradio.Radio(
		label = wording.get('webcam_mode_radio_label'),
		choices = uis_choices.webcam_modes,
		value = 'inline'
	)
	WEBCAM_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('webcam_resolution_dropdown'),
		choices = uis_choices.webcam_resolutions,
		value = uis_choices.webcam_resolutions[0]
	)
	WEBCAM_FPS_SLIDER = gradio.Slider(
		label = wording.get('webcam_fps_slider'),
		value = 25,
		step = 1,
		minimum = 1,
		maximum = 60
	)
	register_ui_component('webcam_mode_radio', WEBCAM_MODE_RADIO)
	register_ui_component('webcam_resolution_dropdown', WEBCAM_RESOLUTION_DROPDOWN)
	register_ui_component('webcam_fps_slider', WEBCAM_FPS_SLIDER)
