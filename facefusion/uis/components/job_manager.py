from typing import Optional, Tuple

import gradio

from facefusion import logger, state_manager, wording
from facefusion.common_helper import get_first
from facefusion.core import create_program
from facefusion.jobs import job_manager, job_store
from facefusion.jobs.job_manager import validate_job
from facefusion.program_helper import import_state, reduce_args
from facefusion.typing import Args
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import JobManagerAction

JOB_MANAGER_GROUP : Optional[gradio.Group] = None
JOB_MANAGER_JOB_ACTION_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_JOB_ID_TEXTBOX : Optional[gradio.Textbox] = None
JOB_MANAGER_JOB_ID_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_STEP_INDEX_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_EXECUTE_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_MANAGER_GROUP
	global JOB_MANAGER_JOB_ACTION_DROPDOWN
	global JOB_MANAGER_JOB_ID_TEXTBOX
	global JOB_MANAGER_JOB_ID_DROPDOWN
	global JOB_MANAGER_STEP_INDEX_DROPDOWN
	global JOB_MANAGER_EXECUTE_BUTTON

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
				JOB_MANAGER_JOB_ID_TEXTBOX = gradio.Textbox(
					label = wording.get('uis.job_manager_job_id_dropdown'),
					max_lines = 1,
					interactive = True
				)
				JOB_MANAGER_JOB_ID_DROPDOWN = gradio.Dropdown(
					label = wording.get('uis.job_manager_job_id_dropdown'),
					choices = job_drafted_ids,
					value = get_first(job_drafted_ids),
					visible = False
				)
				JOB_MANAGER_STEP_INDEX_DROPDOWN = gradio.Dropdown(
					label = wording.get('uis.job_manager_step_index_dropdown'),
					visible = False
				)
			with gradio.Blocks():
				JOB_MANAGER_EXECUTE_BUTTON = gradio.Button(
					value = wording.get('uis.execute_button'),
					variant = 'primary',
					size = 'sm'
				)
		register_ui_component('job_manager_group', JOB_MANAGER_GROUP)


def listen() -> None:
	JOB_MANAGER_JOB_ACTION_DROPDOWN.change(update_job_action, inputs = JOB_MANAGER_JOB_ACTION_DROPDOWN, outputs = [ JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])
	JOB_MANAGER_JOB_ID_DROPDOWN.change(update_job_id, inputs = JOB_MANAGER_JOB_ID_DROPDOWN, outputs = JOB_MANAGER_JOB_ID_DROPDOWN)
	JOB_MANAGER_STEP_INDEX_DROPDOWN.change(update_step_index, inputs = JOB_MANAGER_STEP_INDEX_DROPDOWN,outputs = JOB_MANAGER_STEP_INDEX_DROPDOWN)
	JOB_MANAGER_EXECUTE_BUTTON.click(run, inputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_TEXTBOX ], outputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])


def run(job_action : JobManagerAction, job_id : str, step_index : int) -> Tuple[gradio.Dropdown, gradio.Textbox, gradio.Dropdown, gradio.Dropdown]:
	if job_action == 'job-create':
		if job_manager.create_job(job_id):
			logger.info(wording.get('job_created').format(job_id = job_id), __name__.upper())
			job_drafted_ids = job_manager.find_job_ids('drafted')
			return gradio.Dropdown(value = 'job-add-step'), gradio.Textbox(value = None, visible = False), gradio.Dropdown(choices = job_drafted_ids, value = job_id, visible = True), gradio.Dropdown(choices = [ 0 ], value = 0)
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
		step_args = get_step_args()

		if job_manager.add_step(job_id, step_args):
			logger.info(wording.get('job_step_added').format(job_id = job_id), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_added').format(job_id = job_id), __name__.upper())
	if job_action == 'job-remix-step':
		step_args = get_step_args()

		if job_manager.remix_step(job_id, step_index, step_args):
			logger.info(wording.get('job_remix_step_added').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_remix_step_not_added').format(job_id = job_id, step_index = step_index), __name__.upper())
	if job_action == 'job-insert-step':
		step_args = get_step_args()

		if job_manager.insert_step(job_id, step_index, step_args):
			logger.info(wording.get('job_step_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_inserted').format(job_id = job_id, step_index = step_index), __name__.upper())
	if job_action == 'job-remove-step':
		if job_manager.remove_step(job_id, step_index):
			logger.info(wording.get('job_step_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
		else:
			logger.error(wording.get('job_step_not_removed').format(job_id = job_id, step_index = step_index), __name__.upper())
	return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(), gradio.Dropdown()


def get_step_args() -> Args:
	program = create_program()
	program = import_state(program, job_store.get_step_keys(), state_manager.get_state())
	program = reduce_args(program, job_store.get_step_keys())
	step_args = vars(program.parse_args())
	return step_args


def update_job_action(job_action : JobManagerAction) -> Tuple[gradio.Textbox, gradio.Dropdown, gradio.Dropdown]:
	if job_action == 'job-create':
		return gradio.Textbox(visible = True), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False)
	if job_action in [ 'job-submit', 'job-delete' ]:
		return gradio.Textbox(visible = False), gradio.Dropdown(visible = True), gradio.Dropdown(visible = False)
	if job_action in [ 'job-add-step', 'job-remix-step', 'job-insert-step', 'job-remove-step' ]:
		return gradio.Textbox(visible = False), gradio.Dropdown(visible = True), gradio.Dropdown(visible = True)
	return gradio.Textbox(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False)


def update_job_id(job_id : str) -> gradio.Dropdown:
	print('validate_job', validate_job(job_id))
	# todo: implement validate_job(job_id : str)
	# 1. use this in job_manager.submit_job() instead of count_step_total(job_id)
	# 2. validate json (json.decoder.JSONDecodeError)
	# 3. validate steps exist
	return gradio.Dropdown(value = job_id)


def update_step_index(step_index : int) -> gradio.Dropdown:
	return gradio.Dropdown(value = step_index)
