from typing import Optional
<<<<<<< HEAD
import gradio

from facefusion import wording
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component

=======

import gradio

from facefusion import wording
from facefusion.common_helper import get_first
from facefusion.uis import choices as uis_choices
from facefusion.uis.components.webcam import get_available_webcam_ids
from facefusion.uis.core import register_ui_component

WEBCAM_DEVICE_ID_DROPDOWN : Optional[gradio.Dropdown] = None
>>>>>>> origin/master
WEBCAM_MODE_RADIO : Optional[gradio.Radio] = None
WEBCAM_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
WEBCAM_FPS_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
<<<<<<< HEAD
=======
	global WEBCAM_DEVICE_ID_DROPDOWN
>>>>>>> origin/master
	global WEBCAM_MODE_RADIO
	global WEBCAM_RESOLUTION_DROPDOWN
	global WEBCAM_FPS_SLIDER

<<<<<<< HEAD
=======
	available_webcam_ids = get_available_webcam_ids(0, 10) or [ 'none' ] #type:ignore[list-item]
	WEBCAM_DEVICE_ID_DROPDOWN = gradio.Dropdown(
		value = get_first(available_webcam_ids),
		label = wording.get('uis.webcam_device_id_dropdown'),
		choices = available_webcam_ids
	)
>>>>>>> origin/master
	WEBCAM_MODE_RADIO = gradio.Radio(
		label = wording.get('uis.webcam_mode_radio'),
		choices = uis_choices.webcam_modes,
		value = 'inline'
	)
	WEBCAM_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.webcam_resolution_dropdown'),
		choices = uis_choices.webcam_resolutions,
		value = uis_choices.webcam_resolutions[0]
	)
	WEBCAM_FPS_SLIDER = gradio.Slider(
		label = wording.get('uis.webcam_fps_slider'),
		value = 25,
		step = 1,
		minimum = 1,
		maximum = 60
	)
<<<<<<< HEAD
=======
	register_ui_component('webcam_device_id_dropdown', WEBCAM_DEVICE_ID_DROPDOWN)
>>>>>>> origin/master
	register_ui_component('webcam_mode_radio', WEBCAM_MODE_RADIO)
	register_ui_component('webcam_resolution_dropdown', WEBCAM_RESOLUTION_DROPDOWN)
	register_ui_component('webcam_fps_slider', WEBCAM_FPS_SLIDER)
