from typing import List, Optional, Tuple

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_list, job_manager
from facefusion.typing import JobStatus

JOB_LIST_JOB_DATAFRAME : Optional[gradio.Dataframe] = None
JOB_LIST_JOB_STATUS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
JOB_LIST_REFRESH_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_LIST_JOB_DATAFRAME
	global JOB_LIST_JOB_STATUS_CHECKBOX_GROUP
	global JOB_LIST_REFRESH_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		job_status = get_first(facefusion.choices.job_statuses)
		job_headers, job_contents = job_list.compose_job_list(job_status)

		JOB_LIST_JOB_DATAFRAME = gradio.Dataframe(
			label = wording.get('uis.job_list_dataframe'),
			headers = job_headers,
			value = job_contents,
			show_label = False
		)
		JOB_LIST_JOB_STATUS_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('uis.job_list_status_checkbox_group'),
			choices = facefusion.choices.job_statuses,
			value = job_status,
			show_label = False
		)
		JOB_LIST_REFRESH_BUTTON = gradio.Button(
			value = wording.get('uis.refresh_button'),
			variant = 'primary',
			size = 'sm'
		)


def listen() -> None:
	JOB_LIST_JOB_STATUS_CHECKBOX_GROUP.change(update_job_status_checkbox_group, inputs = JOB_LIST_JOB_STATUS_CHECKBOX_GROUP, outputs = [JOB_LIST_JOB_STATUS_CHECKBOX_GROUP, JOB_LIST_JOB_DATAFRAME])
	JOB_LIST_REFRESH_BUTTON.click(update_job_dataframe, inputs = JOB_LIST_JOB_STATUS_CHECKBOX_GROUP, outputs = JOB_LIST_JOB_DATAFRAME)


def update_job_status_checkbox_group(job_statuses : List[JobStatus]) -> Tuple[gradio.CheckboxGroup, gradio.Dataframe]:
	job_statuses = job_statuses or facefusion.choices.job_statuses
	return gradio.CheckboxGroup(value = job_statuses), update_job_dataframe(job_statuses)


def update_job_dataframe(job_statuses : List[JobStatus]) -> gradio.Dataframe:
	all_job_contents = []

	for job_status in job_statuses:
		_, job_contents = job_list.compose_job_list(job_status)
		all_job_contents.extend(job_contents)
	return gradio.Dataframe(value = all_job_contents)
