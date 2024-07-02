from typing import Optional, List
import gradio

import facefusion.globals
from facefusion import state_manager, wording
from facefusion.uis import choices as uis_choices

COMMON_OPTIONS_CHECKBOX_GROUP : Optional[gradio.Checkboxgroup] = None


def render() -> None:
	global COMMON_OPTIONS_CHECKBOX_GROUP

	common_options = []

	if state_manager.get_item('skip_download'):
		common_options.append('skip-download')
	if facefusion.globals.keep_temp:
		common_options.append('keep-temp')
	if facefusion.globals.skip_audio:
		common_options.append('skip-audio')

	COMMON_OPTIONS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label = wording.get('uis.common_options_checkbox_group'),
		choices = uis_choices.common_options,
		value = common_options
	)


def listen() -> None:
	COMMON_OPTIONS_CHECKBOX_GROUP.change(update, inputs = COMMON_OPTIONS_CHECKBOX_GROUP)


def update(common_options : List[str]) -> None:
	state_manager.set_item('skip_download', 'skip-download' in common_options)
	facefusion.globals.keep_temp = 'keep-temp' in common_options
	facefusion.globals.skip_audio = 'skip-audio' in common_options
