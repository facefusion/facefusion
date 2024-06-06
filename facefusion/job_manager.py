from typing import Optional, List
import glob
import json
import os
import shutil

from facefusion.common_helper import get_current_datetime
from facefusion.filesystem import is_file, is_directory, move_file
from facefusion.typing import Args, Job, JobStatus, JobStep, JobStepStatus

JOBS_PATH : Optional[str] = None
JOB_STATUSES : List[JobStatus] = [ 'queued', 'completed', 'failed' ]


def init_jobs(jobs_path : str) -> bool:
	global JOBS_PATH

	JOBS_PATH = jobs_path
	job_status_paths = [ os.path.join(JOBS_PATH, job_status) for job_status in JOB_STATUSES ]

	for job_status_path in job_status_paths:
		os.makedirs(job_status_path, exist_ok = True)
	return all(is_directory(status_path) for status_path in job_status_paths)


def clear_jobs(jobs_path : str) -> None:
	if is_directory(jobs_path):
		shutil.rmtree(jobs_path)


def create_job(job_id : str) -> bool:
	job : Job =\
	{
		'version': '1',
		'date_created': get_current_datetime(),
		'date_updated': None,
		'steps': []
	}

	return create_job_file(job_id, job)


def delete_job(job_id : str) -> bool:
	return delete_job_file(job_id)


def find_job_ids(job_status : JobStatus) -> List[str]:
	job_pattern = os.path.join(JOBS_PATH, job_status, '*.json')
	job_ids = []

	for job_file in glob.glob(job_pattern):
		job_id, _ = os.path.splitext(os.path.basename(job_file))
		job_ids.append(job_id)
	return sorted(job_ids)


def add_step(job_id : str, step_args : Args) -> bool:
	job = read_job_file(job_id)
	step : JobStep =\
	{
		'args': step_args,
		'status': 'queued'
	}

	if job:
		job.get('steps').append(step)
		return update_job_file(job_id, job)
	return False


def remix_step(job_id : str, step_index : int, step_args : Args) -> bool:
	steps = get_steps(job_id)
	output_path = steps[step_index].get('args').get('output_path')

	if not is_directory(output_path):
		step_args['target_path'] = output_path
		return add_step(job_id, step_args)
	return False


def insert_step(job_id : str, step_index : int, step_args : Args) -> bool:
	job = read_job_file(job_id)
	step : JobStep =\
	{
		'args': step_args,
		'status': 'queued'
	}

	if job:
		job.get('steps').insert(step_index, step)
		return update_job_file(job_id, job)
	return False


def remove_step(job_id : str, step_index : int) -> bool:
	job = read_job_file(job_id)

	if job:
		job.get('steps').pop(step_index)
		return update_job_file(job_id, job)
	return False


def get_steps(job_id : str) -> Optional[List[JobStep]]:
	job = read_job_file(job_id)

	if job:
		return job.get('steps')
	return None


def set_step_status(job_id : str, step_index : int, step_status : JobStepStatus) -> bool:
	job = read_job_file(job_id)
	steps = job.get('steps')

	for index, step in enumerate(steps):
		if index == step_index:
			job.get('steps')[index]['status'] = step_status
			return update_job_file(job_id, job)
	return False


def read_job_file(job_id : str) -> Optional[Job]:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		with open(job_path, 'r') as job_file:
			return json.load(job_file)
	return None


def create_job_file(job_id : str, job : Job) -> bool:
	job_path = suggest_job_path(job_id)

	if not is_file(job_path):
		with open(job_path, 'w') as job_file:
			json.dump(job, job_file, indent = 4)
		return is_file(job_path)
	return False


def update_job_file(job_id : str, job : Job) -> bool:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		with open(job_path, 'w') as job_file:
			job['date_updated'] = get_current_datetime()
			json.dump(job, job_file, indent = 4)
		return is_file(job_path)
	return False


def move_job_file(job_id : str, job_status : JobStatus) -> bool:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		job_move_path = os.path.join(JOBS_PATH, job_status)
		return move_file(job_path, job_move_path)
	return False


def delete_job_file(job_id : str) -> bool:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		os.remove(job_path)
		return not is_file(job_path)
	return False


def suggest_job_path(job_id : str) -> Optional[str]:
	job_file_name = job_id + '.json'
	return os.path.join(JOBS_PATH, 'queued', job_file_name)


def resolve_job_path(job_id : str) -> Optional[str]:
	job_file_name = job_id + '.json'

	for job_status in JOB_STATUSES:
		job_pattern = os.path.join(JOBS_PATH, job_status, job_file_name)
		job_files = glob.glob(job_pattern)

		for job_file in job_files:
			return job_file
	return None
