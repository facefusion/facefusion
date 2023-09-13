from typing import Optional

import gradio

from facefusion import wording
from facefusion.uis import choices
from facefusion.uis import core as ui
from facefusion.uis.typing import Update

WEBCAM_MODE_RADIO : Optional[gradio.Radio] = None


def render() -> None:
	global WEBCAM_MODE_RADIO

	WEBCAM_MODE_RADIO = gradio.Radio(
		label = wording.get('webcam_mode_radio_label'),
		choices = choices.webcam_mode,
		value = 'inline'
	)
	ui.register_component('webcam_mode_radio', WEBCAM_MODE_RADIO)


def update() -> Update:
	return gradio.update(value = None)
