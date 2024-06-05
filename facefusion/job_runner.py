import os

from facefusion.ffmpeg import concat_video
from facefusion.filesystem import is_video, is_directory, move_file
from facefusion.temp_helper import get_temp_file_path, create_temp
from facefusion.job_manager import find_job_ids, get_steps, set_step_status, move_job_file
from facefusion.typing import ProcessStep, JobMergeSet


def run_job(job_id : str, process_step : ProcessStep) -> bool:
	if run_steps(job_id, process_step) and merge_steps(job_id):
		return move_job_file(job_id, 'completed')
	return move_job_file(job_id, 'failed')


def run_all_jobs(process_step : ProcessStep) -> bool:
	job_queued_ids = find_job_ids('queued')

	for job_id in job_queued_ids:
		if not run_job(job_id, process_step):
			return False
	return True


def run_steps(job_id : str, process_step : ProcessStep) -> bool:
	steps = get_steps(job_id)

	for index, step in enumerate(steps):
		step_args = step.get('args')
		output_path = step_args.get('output_path')
		temp_output_path = get_temp_output_path(job_id, index, output_path)

		if not is_directory(output_path):
			step_args['output_path'] = temp_output_path
		if process_step(step_args):
			return set_step_status(job_id, index, 'completed')
		return set_step_status(job_id, index, 'failed')
	return True


def merge_steps(job_id : str) -> bool:
	merge_set = collect_merge_set(job_id)

	for output_path, temp_output_paths in merge_set.items():
		if all(map(is_video, temp_output_paths)):
			if not concat_video(temp_output_paths, output_path):
				return False
		for temp_output_path in temp_output_paths:
			if not move_file(temp_output_path, output_path):
				return False
	return True


def collect_merge_set(job_id : str) -> JobMergeSet:
	steps = get_steps(job_id)
	merge_set : JobMergeSet = {}

	for index, step in enumerate(steps):
		output_path = step.get('args').get('output_path')

		if not is_directory(output_path):
			temp_output_path = get_temp_output_path(job_id, index, output_path)
			merge_set.setdefault(output_path, []).append(temp_output_path)
	return merge_set


def get_temp_output_path(job_id : str, step_index : int, output_path : str) -> str:
	output_file_name = os.path.join(job_id, str(step_index), output_path)
	return get_temp_file_path(output_file_name)
