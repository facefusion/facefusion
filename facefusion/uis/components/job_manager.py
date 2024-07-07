from typing import Optional

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_manager
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component

JOB_MANAGER_GROUP : Optional[gradio.Group] = None
JOB_MANAGER_JOB_ACTION_DROPDOWN  : Optional[gradio.Dropdown] = None
JOB_MANAGER_JOB_ID_DROPDOWN  : Optional[gradio.Dropdown] = None
JOB_MANAGER_STEP_INDEX_DROPDOWN  : Optional[gradio.Dropdown] = None
JOB_MANAGER_APPLY_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_MANAGER_GROUP
	global JOB_MANAGER_JOB_ACTION_DROPDOWN
	global JOB_MANAGER_JOB_ID_DROPDOWN
	global JOB_MANAGER_STEP_INDEX_DROPDOWN
	global JOB_MANAGER_APPLY_BUTTON

	is_job_manager = state_manager.get_item('ui_workflow') == 'job_manager'
	job_drafted_ids = job_manager.find_job_ids('drafted') or ['none']
	with gradio.Group(visible = is_job_manager) as JOB_MANAGER_GROUP:
		with gradio.Blocks():
			JOB_MANAGER_JOB_ACTION_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_manager_job_action_dropdown'),
				choices = uis_choices.job_manager_actions,
				value = get_first(uis_choices.job_manager_actions)
			)
			JOB_MANAGER_JOB_ID_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_manager_job_id_dropdown'),
				choices = job_drafted_ids,
				value = get_first(job_drafted_ids)
			)
			JOB_MANAGER_STEP_INDEX_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_manager_step_index_dropdown'),
				choices = [ 0, 1, 2, 3 ],
				value = 0
			)
		with gradio.Blocks():
			JOB_MANAGER_APPLY_BUTTON = gradio.Button(
				value = wording.get('uis.apply_button'),
				variant = 'primary',
				size = 'sm'
			)
	register_ui_component('job_manager_group', JOB_MANAGER_GROUP)


def listen() -> None:
	pass
