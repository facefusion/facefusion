from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.uis import choices as uis_choices

COMMON_OPTIONS_CHECKBOX_GROUP : Optional[gradio.Checkboxgroup] = None


def render() -> None:
	global COMMON_OPTIONS_CHECKBOX_GROUP

	common_options = []

	if state_manager.get_item('keep_temp'):
		common_options.append('keep-temp')

	COMMON_OPTIONS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label = wording.get('uis.common_options_checkbox_group'),
		choices = uis_choices.common_options,
		value = common_options
	)


def listen() -> None:
	COMMON_OPTIONS_CHECKBOX_GROUP.change(update, inputs = COMMON_OPTIONS_CHECKBOX_GROUP)


def update(common_options : List[str]) -> None:
	keep_temp = 'keep-temp' in common_options
	state_manager.set_item('keep_temp', keep_temp)
