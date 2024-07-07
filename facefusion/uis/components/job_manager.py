from typing import Optional

import gradio

from facefusion import state_manager, wording
from facefusion.uis.core import register_ui_component

JOB_MANAGER_GROUP : Optional[gradio.Group] = None
JOB_MANAGER_APPLY_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_MANAGER_APPLY_BUTTON

	is_job_manager = state_manager.get_item('ui_workflow') == 'job_manager'
	with gradio.Group(visible = is_job_manager) as JOB_MANAGER_GROUP:
		with gradio.Blocks():
			JOB_MANAGER_APPLY_BUTTON = gradio.Button(
				value = wording.get('uis.apply_button'),
				variant = 'primary',
				size = 'sm'
			)
	register_ui_component('job_manager_group', JOB_MANAGER_GROUP)


def listen() -> None:
	pass
