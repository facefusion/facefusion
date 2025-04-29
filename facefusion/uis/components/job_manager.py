from typing import List, Optional, Tuple

import gradio

from facefusion import logger, state_manager, wording
from facefusion.args import collect_step_args
from facefusion.common_helper import get_first, get_last
from facefusion.filesystem import is_directory
from facefusion.jobs import job_manager
from facefusion.types import UiWorkflow
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import get_ui_component
from facefusion.uis.types import JobManagerAction
from facefusion.uis.ui_helper import convert_int_none, convert_str_none, suggest_output_path

JOB_MANAGER_WRAPPER : Optional[gradio.Column] = None
JOB_MANAGER_JOB_ACTION_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_JOB_ID_TEXTBOX : Optional[gradio.Textbox] = None
JOB_MANAGER_JOB_ID_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_STEP_INDEX_DROPDOWN : Optional[gradio.Dropdown] = None
JOB_MANAGER_APPLY_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global JOB_MANAGER_WRAPPER
	global JOB_MANAGER_JOB_ACTION_DROPDOWN
	global JOB_MANAGER_JOB_ID_TEXTBOX
	global JOB_MANAGER_JOB_ID_DROPDOWN
	global JOB_MANAGER_STEP_INDEX_DROPDOWN
	global JOB_MANAGER_APPLY_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_job_manager = state_manager.get_item('ui_workflow') == 'job_manager'
		drafted_job_ids = job_manager.find_job_ids('drafted') or [ 'none' ]

		with gradio.Column(visible = is_job_manager) as JOB_MANAGER_WRAPPER:
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
				choices = drafted_job_ids,
				value = get_last(drafted_job_ids),
				interactive = True,
				visible = False
			)
			JOB_MANAGER_STEP_INDEX_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.job_manager_step_index_dropdown'),
				choices = [ 'none' ],
				value = 'none',
				interactive = True,
				visible = False
			)
			JOB_MANAGER_APPLY_BUTTON = gradio.Button(
				value = wording.get('uis.apply_button'),
				variant = 'primary',
				size = 'sm'
			)


def listen() -> None:
	JOB_MANAGER_JOB_ACTION_DROPDOWN.change(update, inputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_DROPDOWN ], outputs = [ JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])
	JOB_MANAGER_JOB_ID_DROPDOWN.change(update_step_index, inputs = JOB_MANAGER_JOB_ID_DROPDOWN, outputs = JOB_MANAGER_STEP_INDEX_DROPDOWN)
	JOB_MANAGER_APPLY_BUTTON.click(apply, inputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ], outputs = [ JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])

	ui_workflow_dropdown = get_ui_component('ui_workflow_dropdown')
	if ui_workflow_dropdown:
		ui_workflow_dropdown.change(remote_update, inputs = ui_workflow_dropdown, outputs = [ JOB_MANAGER_WRAPPER, JOB_MANAGER_JOB_ACTION_DROPDOWN, JOB_MANAGER_JOB_ID_TEXTBOX, JOB_MANAGER_JOB_ID_DROPDOWN, JOB_MANAGER_STEP_INDEX_DROPDOWN ])


def remote_update(ui_workflow : UiWorkflow) -> Tuple[gradio.Row, gradio.Dropdown, gradio.Textbox, gradio.Dropdown, gradio.Dropdown]:
	is_job_manager = ui_workflow == 'job_manager'
	return gradio.Row(visible = is_job_manager), gradio.Dropdown(value = get_first(uis_choices.job_manager_actions)), gradio.Textbox(value = None, visible = True), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False)


def apply(job_action : JobManagerAction, created_job_id : str, selected_job_id : str, selected_step_index : int) -> Tuple[gradio.Dropdown, gradio.Textbox, gradio.Dropdown, gradio.Dropdown]:
	created_job_id = convert_str_none(created_job_id)
	selected_job_id = convert_str_none(selected_job_id)
	selected_step_index = convert_int_none(selected_step_index)
	step_args = collect_step_args()
	output_path = step_args.get('output_path')

	if is_directory(step_args.get('output_path')):
		step_args['output_path'] = suggest_output_path(step_args.get('output_path'), state_manager.get_item('target_path'))

	if job_action == 'job-create':
		if created_job_id and job_manager.create_job(created_job_id):
			updated_job_ids = job_manager.find_job_ids('drafted') or [ 'none' ]

			logger.info(wording.get('job_created').format(job_id = created_job_id), __name__)
			return gradio.Dropdown(value = 'job-add-step'), gradio.Textbox(visible = False), gradio.Dropdown(value = created_job_id, choices = updated_job_ids, visible = True), gradio.Dropdown()
		else:
			logger.error(wording.get('job_not_created').format(job_id = created_job_id), __name__)

	if job_action == 'job-submit':
		if selected_job_id and job_manager.submit_job(selected_job_id):
			updated_job_ids = job_manager.find_job_ids('drafted') or [ 'none' ]

			logger.info(wording.get('job_submitted').format(job_id = selected_job_id), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(value = get_last(updated_job_ids), choices = updated_job_ids, visible = True), gradio.Dropdown()
		else:
			logger.error(wording.get('job_not_submitted').format(job_id = selected_job_id), __name__)

	if job_action == 'job-delete':
		if selected_job_id and job_manager.delete_job(selected_job_id):
			updated_job_ids = job_manager.find_job_ids('drafted') + job_manager.find_job_ids('queued') + job_manager.find_job_ids('failed') + job_manager.find_job_ids('completed') or [ 'none' ]

			logger.info(wording.get('job_deleted').format(job_id = selected_job_id), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(value = get_last(updated_job_ids), choices = updated_job_ids, visible = True), gradio.Dropdown()
		else:
			logger.error(wording.get('job_not_deleted').format(job_id = selected_job_id), __name__)

	if job_action == 'job-add-step':
		if selected_job_id and job_manager.add_step(selected_job_id, step_args):
			state_manager.set_item('output_path', output_path)
			logger.info(wording.get('job_step_added').format(job_id = selected_job_id), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(visible = True), gradio.Dropdown(visible = False)
		else:
			state_manager.set_item('output_path', output_path)
			logger.error(wording.get('job_step_not_added').format(job_id = selected_job_id), __name__)

	if job_action == 'job-remix-step':
		if selected_job_id and job_manager.has_step(selected_job_id, selected_step_index) and job_manager.remix_step(selected_job_id, selected_step_index, step_args):
			updated_step_choices = get_step_choices(selected_job_id) or [ 'none' ] #type:ignore[list-item]

			state_manager.set_item('output_path', output_path)
			logger.info(wording.get('job_remix_step_added').format(job_id = selected_job_id, step_index = selected_step_index), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(visible = True), gradio.Dropdown(value = get_last(updated_step_choices), choices = updated_step_choices, visible = True)
		else:
			state_manager.set_item('output_path', output_path)
			logger.error(wording.get('job_remix_step_not_added').format(job_id = selected_job_id, step_index = selected_step_index), __name__)

	if job_action == 'job-insert-step':
		if selected_job_id and job_manager.has_step(selected_job_id, selected_step_index) and job_manager.insert_step(selected_job_id, selected_step_index, step_args):
			updated_step_choices = get_step_choices(selected_job_id) or [ 'none' ] #type:ignore[list-item]

			state_manager.set_item('output_path', output_path)
			logger.info(wording.get('job_step_inserted').format(job_id = selected_job_id, step_index = selected_step_index), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(visible = True), gradio.Dropdown(value = get_last(updated_step_choices), choices = updated_step_choices, visible = True)
		else:
			state_manager.set_item('output_path', output_path)
			logger.error(wording.get('job_step_not_inserted').format(job_id = selected_job_id, step_index = selected_step_index), __name__)

	if job_action == 'job-remove-step':
		if selected_job_id and job_manager.has_step(selected_job_id, selected_step_index) and job_manager.remove_step(selected_job_id, selected_step_index):
			updated_step_choices = get_step_choices(selected_job_id) or [ 'none' ] #type:ignore[list-item]

			logger.info(wording.get('job_step_removed').format(job_id = selected_job_id, step_index = selected_step_index), __name__)
			return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(visible = True), gradio.Dropdown(value = get_last(updated_step_choices), choices = updated_step_choices, visible = True)
		else:
			logger.error(wording.get('job_step_not_removed').format(job_id = selected_job_id, step_index = selected_step_index), __name__)
	return gradio.Dropdown(), gradio.Textbox(), gradio.Dropdown(), gradio.Dropdown()


def get_step_choices(job_id : str) -> List[int]:
	steps = job_manager.get_steps(job_id)
	return [ index for index, _ in enumerate(steps) ]


def update(job_action : JobManagerAction, selected_job_id : str) -> Tuple[gradio.Textbox, gradio.Dropdown, gradio.Dropdown]:
	if job_action == 'job-create':
		return gradio.Textbox(value = None, visible = True), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False)

	if job_action == 'job-delete':
		updated_job_ids = job_manager.find_job_ids('drafted') + job_manager.find_job_ids('queued') + job_manager.find_job_ids('failed') + job_manager.find_job_ids('completed') or [ 'none' ]
		updated_job_id = selected_job_id if selected_job_id in updated_job_ids else get_last(updated_job_ids)

		return gradio.Textbox(visible = False), gradio.Dropdown(value = updated_job_id, choices = updated_job_ids, visible = True), gradio.Dropdown(visible = False)

	if job_action in [ 'job-submit', 'job-add-step' ]:
		updated_job_ids = job_manager.find_job_ids('drafted') or [ 'none' ]
		updated_job_id = selected_job_id if selected_job_id in updated_job_ids else get_last(updated_job_ids)

		return gradio.Textbox(visible = False), gradio.Dropdown(value = updated_job_id, choices = updated_job_ids, visible = True), gradio.Dropdown(visible = False)

	if job_action in [ 'job-remix-step', 'job-insert-step', 'job-remove-step' ]:
		updated_job_ids = job_manager.find_job_ids('drafted') or [ 'none' ]
		updated_job_id = selected_job_id if selected_job_id in updated_job_ids else get_last(updated_job_ids)
		updated_step_choices = get_step_choices(updated_job_id) or [ 'none' ] #type:ignore[list-item]

		return gradio.Textbox(visible = False), gradio.Dropdown(value = updated_job_id, choices = updated_job_ids, visible = True), gradio.Dropdown(value = get_last(updated_step_choices), choices = updated_step_choices, visible = True)
	return gradio.Textbox(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False)


def update_step_index(job_id : str) -> gradio.Dropdown:
	step_choices = get_step_choices(job_id) or [ 'none' ] #type:ignore[list-item]
	return gradio.Dropdown(value = get_last(step_choices), choices = step_choices)
