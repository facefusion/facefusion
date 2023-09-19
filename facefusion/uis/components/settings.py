from typing import Optional, List
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.uis import choices
from facefusion.uis.typing import Update

SETTINGS_CHECKBOX_GROUP : Optional[gradio.Checkboxgroup] = None


def render() -> None:
	global SETTINGS_CHECKBOX_GROUP

	value = []
	if facefusion.globals.keep_fps:
		value.append('keep-fps')
	if facefusion.globals.keep_temp:
		value.append('keep-temp')
	if facefusion.globals.skip_audio:
		value.append('skip-audio')
	SETTINGS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label = wording.get('settings_checkbox_group_label'),
		choices = choices.settings,
		value = value
	)


def listen() -> None:
	SETTINGS_CHECKBOX_GROUP.change(update, inputs = SETTINGS_CHECKBOX_GROUP, outputs = SETTINGS_CHECKBOX_GROUP)


def update(settings : List[str]) -> Update:
	facefusion.globals.keep_fps = 'keep-fps' in settings
	facefusion.globals.keep_temp = 'keep-temp' in settings
	facefusion.globals.skip_audio = 'skip-audio' in settings
	return gradio.update(value = settings)
