from typing import Optional

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_manager
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import JobRunnerAction

JOB_RUNNER_GROUP  : Optional[gradio.Group] = None
JOB_RUNNER_JOB_ACTION_DROPDOWN  : Optional[gradio.Dropdown] = None
JOB_RUNNER_JOB_ID_DROPDOWN  : Optional[gradio.Dropdown] = None
JOB_RUNNER_START_BUTTON : Optional[gradio.Button] = None
JOB_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
JOB_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_RUNNER_GROUP
	global JOB_RUNNER_JOB_ACTION_DROPDOWN
	global JOB_RUNNER_JOB_ID_DROPDOWN
	global JOB_RUNNER_START_BUTTON
	global JOB_RUNNER_STOP_BUTTON
	global JOB_RUNNER_CLEAR_BUTTON

	job_manager.init_jobs(state_manager.get_item('jobs_path'))
	is_job_runner = state_manager.get_item('ui_workflow') == 'job_runner'
	job_queued_ids = job_manager.find_job_ids('queued') or [ 'none' ]
	with gradio.Group(visible = is_job_runner) as JOB_RUNNER_GROUP:
		with gradio.Blocks():
			JOB_RUNNER_JOB_ACTION_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_runner_job_action_dropdown'),
				choices = uis_choices.job_runner_actions,
				value = get_first(uis_choices.job_runner_actions)
			)
			JOB_RUNNER_JOB_ID_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_runner_job_id_dropdown'),
				choices = job_queued_ids,
				value = get_first(job_queued_ids)
			)
		with gradio.Blocks():
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
	JOB_RUNNER_JOB_ACTION_DROPDOWN.change(update_job_action, inputs = JOB_RUNNER_JOB_ACTION_DROPDOWN, outputs = JOB_RUNNER_JOB_ID_DROPDOWN)
	JOB_RUNNER_JOB_ID_DROPDOWN.change(update_job_id, inputs = [ JOB_RUNNER_JOB_ACTION_DROPDOWN, JOB_RUNNER_JOB_ID_DROPDOWN ], outputs = JOB_RUNNER_JOB_ID_DROPDOWN)


def update_job_action(job_action : JobRunnerAction) -> gradio.Dropdown:
	job_queued_ids = job_manager.find_job_ids('queued') or [ 'none ']
	job_failed_ids = job_manager.find_job_ids('failed') or [ 'none ']

	if job_action == 'job-run':
		return gradio.Dropdown(visible = True, value = get_first(job_queued_ids), choices = job_queued_ids)
	if job_action == 'job-retry':
		return gradio.Dropdown(visible = True, value = get_first(job_failed_ids), choices = job_failed_ids)
	return gradio.Dropdown(visible = False, value = None, choices = None)


def update_job_id(job_action : JobRunnerAction, job_id : str) -> gradio.Dropdown:
	print('todo: implement validation', job_action, job_id)
	return gradio.Dropdown()
