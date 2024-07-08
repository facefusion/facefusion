from typing import Optional, Tuple

import gradio

from facefusion import logger, state_manager, wording
from facefusion.common_helper import get_first
from facefusion.jobs import job_manager
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import JobManagerAction

JOB_MANAGER_GROUP : Optional[gradio.Group] = None
JOB_MANAGER_JOB_ACTION_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_JOB_ID_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_STEP_INDEX_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_APPLY_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_MANAGER_GROUP
	global JOB_MANAGER_JOB_ACTION_DROPDOWN
	global JOB_MANAGER_JOB_ID_DROPDOWN
	global JOB_MANAGER_STEP_INDEX_DROPDOWN
	global JOB_MANAGER_APPLY_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_job_manager = state_manager.get_item('ui_workflow') == 'job_manager'
		job_drafted_ids = job_manager.find_job_ids('drafted') or ['none']

		with gradio.Group(visible = is_job_manager) as JOB_MANAGER_GROUP:
			with gradio.Blocks():
				JOB_MANAGER_JOB_ACTION_DROPDOWN = gradio.Dropdown(
					label = wording.get('uis.job_manager_job_action_dropdown'),
					choices = uis_choices.job_manager_actions,
					value = get_first(uis_choices.job_manager_actions)
				)
				# todo: dont show job id on job-create action and initially
				JOB_MANAGER_JOB_ID_DROPDOWN = gradio.Dropdown(
					label = wording.get('uis.job_manager_job_id_dropdown'),
					choices = job_drafted_ids,
					value = get_first(job_drafted_ids)
				)
				# todo: only show step index on step related actions
				JOB_MANAGER_STEP_INDEX_DROPDOWN = gradio.Dropdown(
					label = wording.get('uis.job_manager_step_index_dropdown'),
					choices = [ 0, 1, 2, 3 ], #todo: read actual step
					value = 0 # todo: select first from choices
				)
			with gradio.Blocks():
				JOB_MANAGER_APPLY_BUTTON = gradio.Button(
					value = wording.get('uis.apply_button'),
					variant = 'primary',
					size = 'sm'
				)
		register_ui_component('job_manager_group', JOB_MANAGER_GROUP)


def listen() -> None:
	JOB_MANAGER_JOB_ACTION_DROPDOWN.change(update_job_action, inputs = JOB_MANAGER_JOB_ACTION_DROPDOWN, outputs = JOB_MANAGER_JOB_ID_DROPDOWN)
	JOB_MANAGER_JOB_ID_DROPDOWN.change(update_job_id, inputs = JOB_MANAGER_JOB_ID_DROPDOWN, outputs = JOB_MANAGER_JOB_ID_DROPDOWN)
	JOB_MANAGER_STEP_INDEX_DROPDOWN.change(update_step_index, inputs = JOB_MANAGER_STEP_INDEX_DROPDOWN,outputs = JOB_MANAGER_STEP_INDEX_DROPDOWN)
	JOB_MANAGER_APPLY_BUTTON.click(apply, inputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ], outputs = [ JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])


def apply(job_action : JobManagerAction, job_id : str, step_index : int) -> Tuple[gradio.Dropdown, gradio.Dropdown]:
	if job_action == 'job-create':
		if job_manager.create_job(job_id):
			logger.info(wording.get('job_created').format(job_id = job_id), __name__.upper())
		else:
			logger.error(wording.get('job_not_created').format(job_id = job_id), __name__.upper())
	if job_action == 'job-submit':
		if job_manager.submit_job(job_id):
			logger.info(wording.get('job_submitted').format(job_id = job_id), __name__.upper())
		else:
			logger.error(wording.get('job_not_submitted').format(job_id = job_id), __name__.upper())
	if job_action == 'job-submit-all':
		if job_manager.submit_jobs():
			logger.info(wording.get('job_all_submitted'), __name__.upper())
		else:
			logger.error(wording.get('job_all_not_submitted'), __name__.upper())
	if job_action == 'job-delete':
		if job_manager.delete_job(job_id):
			logger.info(wording.get('job_deleted').format(job_id = job_id), __name__.upper())
		else:
			logger.error(wording.get('job_not_deleted').format(job_id = job_id), __name__.upper())
	if job_action == 'job-delete-all':
		if job_manager.delete_jobs():
			logger.info(wording.get('job_all_deleted'), __name__.upper())
		else:
			logger.error(wording.get('job_all_not_deleted'), __name__.upper())
	if job_action == 'job-add-step':
		print('todo: implement step args')
		if job_manager.add_step(job_id, {}):
			logger.info(wording.get('job_step_added').format(job_id = job_id), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_added').format(job_id = job_id), __name__.upper())
	if job_action == 'job-remix-step':
		print('todo: implement step args')
		if job_manager.remix_step(job_id, step_index, {}):
			logger.info(wording.get('job_remix_step_added').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_remix_step_not_added').format(job_id = job_id, step_index = step_index), __name__.upper())
	if job_action == 'job-insert-step':
		print('todo: implement step args')
		if job_manager.insert_step(job_id, step_index, {}):
			logger.info(wording.get('job_step_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
	if job_action == 'job-remove-step':
		if job_manager.remove_step(job_id, step_index):
			logger.info(wording.get('job_step_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
	return gradio.Dropdown(), gradio.Dropdown()


def update_job_action(job_action : JobManagerAction) -> gradio.Dropdown:
	print(job_action)
	return gradio.Dropdown()


def update_job_id(job_id : str) -> gradio.Dropdown:
	# todo: implement validate_job(job_id : str)
	# 1. use this in job_manager.submit_job() instead of count_step_total(job_id)
	# 2. validate json (json.decoder.JSONDecodeError)
	# 3. validate steps exist
	return gradio.Dropdown(value = job_id)


def update_step_index(step_index : int) -> gradio.Dropdown:
	return gradio.Dropdown(value = step_index)
