from typing import Optional, List
import sys
import json
import os
import shutil
from argparse import ArgumentParser
from datetime import datetime

from facefusion.filesystem import is_file, is_directory
from facefusion.typing import JobStep, Job, JobArgs, JobStepStatus, JobStepAction, JobStatus
from facefusion.common_helper import get_argument_key

JOBS_PATH : Optional[str] = None
JOB_STATUSES : List[JobStatus] = [ 'queued', 'completed', 'failed' ]
ARGS_ACTION_REGISTRY : Optional[List[str]] = None
ARGS_RUN_REGISTRY : Optional[List[str]] = None


def get_current_datetime() -> str:
	return datetime.now().astimezone().isoformat()


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


def register_action_args(args : List[str]) -> None:
	global ARGS_ACTION_REGISTRY

	if ARGS_ACTION_REGISTRY is None:
		ARGS_ACTION_REGISTRY = []

	for arg in args:
		ARGS_ACTION_REGISTRY.append(arg)


def register_run_args(args : List[str]) -> None:
	global ARGS_RUN_REGISTRY

	if ARGS_RUN_REGISTRY is None:
		ARGS_RUN_REGISTRY = []

	for arg in args:
		ARGS_RUN_REGISTRY.append(arg)


def resolve_job_path(job_id : str) -> str:
	job_file_name = job_id + '.json'

	for job_status in JOB_STATUSES:
		if job_file_name in os.listdir(os.path.join(JOBS_PATH, job_status)):
			return os.path.join(JOBS_PATH, job_status, job_file_name)
	return os.path.join(JOBS_PATH, 'queued', job_file_name)


def create_step(args : JobArgs) -> JobStep:
	step : JobStep =\
	{
		'action': 'process',
		'args': args,
		'status': 'queued'
	}
	return step


def create_job(job_id : str) -> bool:
	job : Job =\
	{
		'version': '1',
		'date_created': get_current_datetime(),
		'date_updated': None,
		'steps': []
	}
	job_path = resolve_job_path(job_id)
	if not is_file(job_path):
		return write_job_file(job_id, job)
	return False


def add_step(job_id : str, args : JobArgs) -> bool:
	job = read_job_file(job_id)

	if job:
		step = create_step(args)
		job.get('steps').append(step)
		return update_job_file(job_id, job)
	return False


def remix_step(job_id : str, args : JobArgs) -> bool:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		if steps:
			previous_output_path = steps[-1].get('args').get('output_path')
			if not is_directory(previous_output_path):
				args['target_path'] = previous_output_path
				return add_step(job_id, args) and set_step_action(job_id, len(steps), 'remix')
	return False


def insert_step(job_id : str, step_index : int, args : JobArgs) -> bool:
	job = read_job_file(job_id)

	if job:
		step = create_step(args)
		if step_index < 0:
			step_index = len(job.get('steps')) + step_index + 1
		job.get('steps').insert(step_index, step)
		return update_job_file(job_id, job)
	return False


def remove_step(job_id : str, step_index : int) -> bool:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		step_length = len(steps)
		if step_index in range(-step_length, step_length):
			job.get('steps').pop(step_index)
			return update_job_file(job_id, job)
	return False


def set_step_status(job_id : str, step_index : int, step_status : JobStepStatus) -> bool:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		if step_index in range(len(steps)):
			job.get('steps')[step_index]['status'] = step_status
			return update_job_file(job_id, job)
	return False


def get_step_status(job_id : str, step_index : int) -> Optional[JobStepStatus]:
	job = read_job_file(job_id)

	if job:
		steps : List[JobStep] = job.get('steps')
		if step_index in range(len(steps)):
			return steps[step_index].get('status')
	return None


def set_step_action(job_id : str, step_index : int, action : JobStepAction) -> bool:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		if step_index in range(len(steps)):
			job.get('steps')[step_index]['action'] = action
			return update_job_file(job_id, job)
	return False


def read_job_file(job_id : str) -> Optional[Job]:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		with open(job_path, 'r') as job_file:
			return json.load(job_file)
	return None


def write_job_file(job_id : str, job : Job) -> bool:
	job_path = resolve_job_path(job_id)

	with open(job_path, 'w') as job_file:
		json.dump(job, job_file, indent = 4)
	return is_file(job_path)


def update_job_file(job_id : str, job : Job) -> bool:
	job['date_updated'] = get_current_datetime()
	return write_job_file(job_id, job)


def move_job_file(job_id : str, job_status : JobStatus) -> bool:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		job_file_path_moved = shutil.move(job_path, os.path.join(JOBS_PATH, job_status))
		return is_file(job_file_path_moved)
	return False


def delete_job_file(job_id : str) -> bool:
	job_path = resolve_job_path(job_id)

	if is_file(job_path):
		os.remove(job_path)
		return True
	return False


def get_job_ids(job_status : JobStatus) -> List[str]:
	job_ids = []
	job_file_names = os.listdir(os.path.join(JOBS_PATH, job_status))

	for job_file_name in job_file_names:
		if is_file(os.path.join(JOBS_PATH, job_status, job_file_name)):
			job_ids.append(os.path.splitext(job_file_name)[0])
	return job_ids


def get_job_status(job_id : str) -> Optional[JobStatus]:
	for job_status in JOB_STATUSES:
		if job_id in get_job_ids(job_status):
			return job_status
	return None


def get_step_total(job_id : str) -> int:
	job = read_job_file(job_id)

	if job:
		steps = job.get('steps')
		return len(steps)
	return 0


def filter_step_args(program : ArgumentParser) -> JobArgs:
	args = program.parse_args()
	step_args_keys = { get_argument_key(program, arg) for arg in ARGS_ACTION_REGISTRY }
	step_args = {}

	for key, value in vars(args).items():
		if key in step_args_keys:
			step_args[key] = value
	return step_args


def has_job_action() -> bool:
	return any(argv.startswith('--job') for argv in sys.argv)
