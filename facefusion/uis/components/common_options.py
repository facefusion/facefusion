<<<<<<< HEAD
from typing import Optional, List
import gradio

import facefusion.globals
from facefusion import wording
=======
from typing import List, Optional

import gradio

from facefusion import state_manager, wording
>>>>>>> origin/master
from facefusion.uis import choices as uis_choices

COMMON_OPTIONS_CHECKBOX_GROUP : Optional[gradio.Checkboxgroup] = None


def render() -> None:
	global COMMON_OPTIONS_CHECKBOX_GROUP

<<<<<<< HEAD
	value = []
	if facefusion.globals.keep_temp:
		value.append('keep-temp')
	if facefusion.globals.skip_audio:
		value.append('skip-audio')
	if facefusion.globals.skip_download:
		value.append('skip-download')
	COMMON_OPTIONS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label = wording.get('uis.common_options_checkbox_group'),
		choices = uis_choices.common_options,
		value = value
=======
	common_options = []

	if state_manager.get_item('keep_temp'):
		common_options.append('keep-temp')
	if state_manager.get_item('skip_audio'):
		common_options.append('skip-audio')

	COMMON_OPTIONS_CHECKBOX_GROUP = gradio.Checkboxgroup(
		label = wording.get('uis.common_options_checkbox_group'),
		choices = uis_choices.common_options,
		value = common_options
>>>>>>> origin/master
	)


def listen() -> None:
	COMMON_OPTIONS_CHECKBOX_GROUP.change(update, inputs = COMMON_OPTIONS_CHECKBOX_GROUP)


def update(common_options : List[str]) -> None:
<<<<<<< HEAD
	facefusion.globals.keep_temp = 'keep-temp' in common_options
	facefusion.globals.skip_audio = 'skip-audio' in common_options
	facefusion.globals.skip_download = 'skip-download' in common_options
=======
	keep_temp = 'keep-temp' in common_options
	skip_audio = 'skip-audio' in common_options
	state_manager.set_item('keep_temp', keep_temp)
	state_manager.set_item('skip_audio', skip_audio)
>>>>>>> origin/master
