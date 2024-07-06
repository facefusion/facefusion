from typing import Optional

import gradio

from facefusion import state_manager, wording
from facefusion.uis.core import register_ui_component

JOB_RUNNER_GROUP  : Optional[gradio.Group] = None
JOB_RUNNER_START_BUTTON : Optional[gradio.Button] = None
JOB_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
JOB_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_RUNNER_GROUP
	global JOB_RUNNER_START_BUTTON
	global JOB_RUNNER_STOP_BUTTON
	global JOB_RUNNER_CLEAR_BUTTON

	with gradio.Group(visible = state_manager.get_item('ui_workflow') == 'job_runner') as JOB_RUNNER_GROUP:
		with gradio.Row():
			JOB_RUNNER_START_BUTTON = gradio.Button(
				value = wording.get('uis.start_button'),
				variant = 'primary',
				size = 'sm'
			)
			JOB_RUNNER_STOP_BUTTON = gradio.Button(
				value = wording.get('uis.stop_button'),
				variant = 'primary',
				size = 'sm',
				visible = False
			)
			JOB_RUNNER_CLEAR_BUTTON = gradio.Button(
				value = wording.get('uis.clear_button'),
				size = 'sm'
			)
	register_ui_component('job_runner_group', JOB_RUNNER_GROUP)


def listen() -> None:
	pass


