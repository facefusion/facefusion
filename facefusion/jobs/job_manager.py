import os
from copy import copy
from typing import List, Optional

import facefusion.choices
from facefusion.date_helper import get_current_date_time
from facefusion.filesystem import create_directory, get_file_name, is_directory, is_file, move_file, remove_directory, remove_file, resolve_file_pattern
from facefusion.jobs.job_helper import get_step_output_path
from facefusion.json import read_json, write_json
from facefusion.types import Args, Job, JobSet, JobStatus, JobStep, JobStepStatus

JOBS_PATH : Optional[str] = None


def init_jobs(jobs_path : str) -> bool:
	global JOBS_PATH

	JOBS_PATH = jobs_path
	job_status_paths = [ os.path.join(JOBS_PATH, job_status) for job_status in facefusion.choices.job_statuses ]

	for job_status_path in job_status_paths:
		create_directory(job_status_path)
	return all(is_directory(status_path) for status_path in job_status_paths)


def clear_jobs(jobs_path : str) -> bool:
	return remove_directory(jobs_path)


def create_job(job_id : str) -> bool:
	job : Job =\
	{
		'version': '1',
		'date_created': get_current_date_time().isoformat(),
		'date_updated': None,
		'steps': []
	}

	return create_job_file(job_id, job)


def submit_job(job_id : str) -> bool:
	drafted_job_ids = find_job_ids('drafted')
	steps = get_steps(job_id)

	if job_id in drafted_job_ids and steps:
		return set_steps_status(job_id, 'queued') and move_job_file(job_id, 'queued')
	return False


def submit_jobs(halt_on_error : bool) -> bool:
	drafted_job_ids = find_job_ids('drafted')
	has_error = False

	if drafted_job_ids:
		for job_id in drafted_job_ids:
			if not submit_job(job_id):
				has_error = True
				if halt_on_error:
					return False
		return not has_error
	return False


def delete_job(job_id : str) -> bool:
	return delete_job_file(job_id)


def delete_jobs(halt_on_error : bool) -> bool:
	job_ids = find_job_ids('drafted') + find_job_ids('queued') + find_job_ids('failed') + find_job_ids('completed')
	has_error = False

	if job_ids:
		for job_id in job_ids:
			if not delete_job(job_id):
				has_error = True
				if halt_on_error:
					return False
		return not has_error
	return False


def find_jobs(job_status : JobStatus) -> JobSet:
	job_ids = find_job_ids(job_status)
	job_set : JobSet = {}

	for job_id in job_ids:
		job_set[job_id] = read_job_file(job_id)
	return job_set


def find_job_ids(job_status : JobStatus) -> List[str]:
	job_pattern = os.path.join(JOBS_PATH, job_status, '*.json')
	job_paths = resolve_file_pattern(job_pattern)
	job_paths.sort(key = os.path.getmtime)
	job_ids = []

	for job_path in job_paths:
		job_id = get_file_name(job_path)
		job_ids.append(job_id)
	return job_ids


def validate_job(job_id : str) -> bool:
	job = read_job_file(job_id)
	return bool(job and 'version' in job and 'date_created' in job and 'date_updated' in job and 'steps' in job)


def has_step(job_id : str, step_index : int) -> bool:
	step_total = count_step_total(job_id)
	return step_index in range(step_total)


def add_step(job_id : str, step_args : Args) -> bool:
	job = read_job_file(job_id)

	if job:
		job.get('steps').append(
		{
			'args': step_args,
			'status': 'drafted'
		})
		return update_job_file(job_id, job)
	return False


def remix_step(job_id : str, step_index : int, step_args : Args) -> bool:
	steps = get_steps(job_id)
	step_args = copy(step_args)

	if step_index and step_index < 0:
		step_index = count_step_total(job_id) - 1

	if has_step(job_id, step_index):
		output_path = steps[step_index].get('args').get('output_path')
		step_args['target_path'] = get_step_output_path(job_id, step_index, output_path)
		return add_step(job_id, step_args)
	return False


def insert_step(job_id : str, step_index : int, step_args : Args) -> bool:
	job = read_job_file(job_id)
	step_args = copy(step_args)

	if step_index and step_index < 0:
		step_index = count_step_total(job_id) - 1

	if job and has_step(job_id, step_index):
		job.get('steps').insert(step_index,
		{
			'args': step_args,
			'status': 'drafted'
		})
		return update_job_file(job_id, job)
	return False


def remove_step(job_id : str, step_index : int) -> bool:
	job = read_job_file(job_id)

	if step_index and step_index < 0:
		step_index = count_step_total(job_id) - 1

	if job and has_step(job_id, step_index):
		job.get('steps').pop(step_index)
		return update_job_file(job_id, job)
	return False


def get_steps(job_id : str) -> List[JobStep]:
	job = read_job_file(job_id)

	if job:
		return job.get('steps')
	return []


def count_step_total(job_id : str) -> int:
	steps = get_steps(job_id)

	if steps:
		return len(steps)
	return 0


def set_step_status(job_id : str, step_index : int, step_status : JobStepStatus) -> bool:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		if has_step(job_id, step_index):
			steps[step_index]['status'] = step_status
			return update_job_file(job_id, job)
	return False


def set_steps_status(job_id : str, step_status : JobStepStatus) -> bool:
	job = read_job_file(job_id)

	if job:
		for step in job.get('steps'):
			step['status'] = step_status
		return update_job_file(job_id, job)
	return False


def read_job_file(job_id : str) -> Optional[Job]:
	job_path = find_job_path(job_id)
	return read_json(job_path) #type:ignore[return-value]


def create_job_file(job_id : str, job : Job) -> bool:
	job_path = find_job_path(job_id)

	if not is_file(job_path):
		job_create_path = suggest_job_path(job_id, 'drafted')
		return write_json(job_create_path, job) #type:ignore[arg-type]
	return False


def update_job_file(job_id : str, job : Job) -> bool:
	job_path = find_job_path(job_id)

	if is_file(job_path):
		job['date_updated'] = get_current_date_time().isoformat()
		return write_json(job_path, job) #type:ignore[arg-type]
	return False


def move_job_file(job_id : str, job_status : JobStatus) -> bool:
	job_path = find_job_path(job_id)
	job_move_path = suggest_job_path(job_id, job_status)
	return move_file(job_path, job_move_path)


def delete_job_file(job_id : str) -> bool:
	job_path = find_job_path(job_id)
	return remove_file(job_path)


def suggest_job_path(job_id : str, job_status : JobStatus) -> Optional[str]:
	job_file_name = get_job_file_name(job_id)

	if job_file_name:
		return os.path.join(JOBS_PATH, job_status, job_file_name)
	return None


def find_job_path(job_id : str) -> Optional[str]:
	job_file_name = get_job_file_name(job_id)

	if job_file_name:
		for job_status in facefusion.choices.job_statuses:
			job_pattern = os.path.join(JOBS_PATH, job_status, job_file_name)
			job_paths = resolve_file_pattern(job_pattern)

			for job_path in job_paths:
				return job_path
	return None


def get_job_file_name(job_id : str) -> Optional[str]:
	if job_id:
		return job_id + '.json'
	return None
