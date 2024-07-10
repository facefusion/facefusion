from typing import List, Optional, Tuple

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_manager
from facefusion.typing import JobStatus
from facefusion.uis.components.job_list import update_job_dataframe
from facefusion.uis.core import get_ui_component, register_ui_component

JOB_LIST_JOB_STATUS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global JOB_LIST_JOB_STATUS_CHECKBOX_GROUP

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		job_status = get_first(facefusion.choices.job_statuses)

		JOB_LIST_JOB_STATUS_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('uis.job_list_status_checkbox_group'),
			choices = facefusion.choices.job_statuses,
			value = job_status
		)
		register_ui_component('job_list_job_status_checkbox_group', JOB_LIST_JOB_STATUS_CHECKBOX_GROUP)


def listen() -> None:
	job_list_job_dataframe = get_ui_component('job_list_job_dataframe')
	JOB_LIST_JOB_STATUS_CHECKBOX_GROUP.change(update_job_status_checkbox_group, inputs = JOB_LIST_JOB_STATUS_CHECKBOX_GROUP, outputs = [ JOB_LIST_JOB_STATUS_CHECKBOX_GROUP, job_list_job_dataframe ])


def update_job_status_checkbox_group(job_statuses : List[JobStatus]) -> Tuple[gradio.CheckboxGroup, gradio.Dataframe]:
	job_statuses = job_statuses or facefusion.choices.job_statuses
	return gradio.CheckboxGroup(value = job_statuses), update_job_dataframe(job_statuses)
