from typing import List, Optional

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_list, job_manager
from facefusion.types import JobStatus
from facefusion.uis.core import get_ui_component

JOB_LIST_JOBS_DATAFRAME : Optional[gradio.Dataframe] = None
JOB_LIST_REFRESH_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_LIST_JOBS_DATAFRAME
	global JOB_LIST_REFRESH_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		job_status = get_first(facefusion.choices.job_statuses)
		job_headers, job_contents = job_list.compose_job_list(job_status)

		JOB_LIST_JOBS_DATAFRAME = gradio.Dataframe(
			headers = job_headers,
			value = job_contents,
			datatype = [ 'str', 'number', 'date', 'date', 'str' ],
			show_label = False
		)
		JOB_LIST_REFRESH_BUTTON = gradio.Button(
			value = wording.get('uis.refresh_button'),
			variant = 'primary',
			size = 'sm'
		)


def listen() -> None:
	job_list_job_status_checkbox_group = get_ui_component('job_list_job_status_checkbox_group')
	if job_list_job_status_checkbox_group:
		job_list_job_status_checkbox_group.change(update_job_dataframe, inputs = job_list_job_status_checkbox_group, outputs = JOB_LIST_JOBS_DATAFRAME)
		JOB_LIST_REFRESH_BUTTON.click(update_job_dataframe, inputs = job_list_job_status_checkbox_group, outputs = JOB_LIST_JOBS_DATAFRAME)


def update_job_dataframe(job_statuses : List[JobStatus]) -> gradio.Dataframe:
	all_job_contents = []

	for job_status in job_statuses:
		_, job_contents = job_list.compose_job_list(job_status)
		all_job_contents.extend(job_contents)
	return gradio.Dataframe(value = all_job_contents)
