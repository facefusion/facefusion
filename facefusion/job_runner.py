import os
import shutil
from typing import Dict, List
from facefusion.ffmpeg import concat_video
from facefusion.filesystem import is_video, create_temp, get_temp_file_path, is_directory, is_file
from facefusion.job_manager import read_job_file, set_step_status, move_job_file, get_job_ids
from facefusion.typing import JobStep, HandleStep


def run_job(job_id : str, handle_step : HandleStep) -> bool:
	job = read_job_file(job_id)
	steps = job.get('steps')

	if run_steps(job_id, steps, handle_step) and merge_steps(job_id):
		return move_job_file(job_id, 'completed')
	return move_job_file(job_id, 'failed')


def run_all_jobs(handle_step : HandleStep) -> bool:
	job_queued_ids = get_job_ids('queued')

	for job_id in job_queued_ids:
		if not run_job(job_id, handle_step):
			return False
	return True


def run_steps(job_id : str, steps : List[JobStep], handle_step : HandleStep) -> bool:
	for step_index, step in enumerate(steps):
		step_args = step.get('args')
		output_path = step_args.get('output_path')
		target_path = step_args.get('target_path')

		if not is_directory(output_path):
			step_args['output_path'] = get_temp_output_path(output_path, job_id, step_index)
		if step.get('action') == 'remix':
			step_args['target_path'] = get_temp_output_path(target_path, job_id, step_index - 1)
		if handle_step(step_args):
			return set_step_status(job_id, step_index, 'completed')
		return set_step_status(job_id, step_index, 'failed')
	return True


def merge_steps(job_id : str) -> bool:
	merge_set = collect_merge_set(job_id)

	for output_path, temp_output_paths in merge_set.items():
		if all(map(is_video, temp_output_paths)):
			return concat_video(temp_output_paths, output_path)
		for temp_output_path in temp_output_paths:
			if not move_file(temp_output_path, output_path):
				return False
	return True


def collect_merge_set(job_id : str) -> Dict[str, List[str]]:
	job = read_job_file(job_id)
	steps = job.get('steps')
	merge_set : Dict[str, List[str]] = {}

	for step_index, step in enumerate(steps):
		output_path = step.get('args').get('output_path')
		if not is_directory(output_path):
			temp_output_path = get_temp_output_path(output_path, job_id, step_index)

			if output_path not in merge_set.keys():
				merge_set[output_path] = [ temp_output_path ]
			else:
				merge_set[output_path].append(temp_output_path)
	return merge_set


def get_temp_output_path(output_path : str, job_id : str, step_index : int) -> str: # TODO: refactor
	output_file_name = "{}_{}_{}".format(job_id, str(step_index), os.path.basename(output_path))
	temp_output_path = get_temp_file_path(output_file_name)
	create_temp(output_file_name)
	return temp_output_path


def move_file(input_path : str, output_path : str) -> bool: # TODO: refactor
	if is_file(input_path):
		shutil.move(input_path, output_path)
		return is_file(output_path)
	return False
