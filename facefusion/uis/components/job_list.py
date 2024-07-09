from typing import List, Optional, Tuple

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.job_list import compose_job_list
from facefusion.jobs import job_manager
from facefusion.typing import JobStatus
from facefusion.uis.core import register_ui_component

JOB_LIST_DATAFRAME : Optional[gradio.Dataframe] = None
JOB_LIST_STATUS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
JOB_LIST_UPDATE_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_LIST_DATAFRAME
	global JOB_LIST_STATUS_CHECKBOX_GROUP
	global JOB_LIST_UPDATE_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		job_headers, job_contents = compose_job_list(facefusion.choices.job_statuses[0])

		JOB_LIST_DATAFRAME = gradio.Dataframe(
			label = wording.get('uis.job_list_dataframe'),
			headers = job_headers,
			value = job_contents,
			show_label = False,
		)
		JOB_LIST_STATUS_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('uis.job_list_status_checkbox_group'),
			choices = facefusion.choices.job_statuses,
			value = facefusion.choices.job_statuses[0],
			show_label = False,

		)
		JOB_LIST_UPDATE_BUTTON = gradio.Button(
			value = wording.get('uis.job_list_update_button'),
			variant = 'primary',
			size = 'sm'
		)
		register_ui_component('job_list_dataframe', JOB_LIST_DATAFRAME)
		register_ui_component('job_list_status_checkbox_group', JOB_LIST_STATUS_CHECKBOX_GROUP)
		register_ui_component('job_list_update_button', JOB_LIST_UPDATE_BUTTON)


def listen() -> None:
	JOB_LIST_STATUS_CHECKBOX_GROUP.change(update_status_checkbox_group, inputs = JOB_LIST_STATUS_CHECKBOX_GROUP, outputs = [JOB_LIST_STATUS_CHECKBOX_GROUP, JOB_LIST_DATAFRAME])
	JOB_LIST_UPDATE_BUTTON.click(update_job_list, inputs = JOB_LIST_STATUS_CHECKBOX_GROUP, outputs = JOB_LIST_DATAFRAME)


def update_status_checkbox_group(job_statuses : List[JobStatus]) -> Tuple[gradio.CheckboxGroup, gradio.Dataframe]:
	job_statuses = job_statuses or facefusion.choices.job_statuses
	return gradio.CheckboxGroup(value = job_statuses), update_job_list(job_statuses)


def update_job_list(job_statuses : List[JobStatus]) -> gradio.Dataframe:
	job_contents = None
	for job_status in job_statuses:
		if job_contents is None:
			job_contents = compose_job_list(job_status)[1]
		else:
			job_contents.extend(compose_job_list(job_status)[1])
	return gradio.Dataframe(value = job_contents)
