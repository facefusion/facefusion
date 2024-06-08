from facefusion.ffmpeg import concat_video
from facefusion.filesystem import is_image, is_video, move_file
from facefusion.job_helper import get_step_output_path
from facefusion.job_manager import find_job_ids, get_steps, set_step_status, move_job_file
from facefusion.typing import ProcessStep, JobMergeSet


def run_job(job_id : str, process_step : ProcessStep) -> bool:
	if run_steps(job_id, process_step) and finalize_steps(job_id):
		return move_job_file(job_id, 'completed')
	return move_job_file(job_id, 'failed')


def run_jobs(process_step : ProcessStep) -> bool:
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
		step_output_path = get_step_output_path(job_id, index, output_path)

		if step_output_path:
			step_args['output_path'] = step_output_path
		if process_step(step_args):
			return set_step_status(job_id, index, 'completed')
		return set_step_status(job_id, index, 'failed')
	return True


def finalize_steps(job_id : str) -> bool:
	merge_set = collect_merge_set(job_id)

	for output_path, temp_output_paths in merge_set.items():
		if any(map(is_image, temp_output_paths)):
			for temp_output_path in temp_output_paths:
				if not move_file(temp_output_path, output_path):
					return False
		if all(map(is_video, temp_output_paths)):
			return concat_video(temp_output_paths, output_path)
	return True


def collect_merge_set(job_id : str) -> JobMergeSet:
	steps = get_steps(job_id)
	merge_set : JobMergeSet = {}

	for index, step in enumerate(steps):
		output_path = step.get('args').get('output_path')
		step_output_path = get_step_output_path(job_id, index, output_path)

		if step_output_path:
			merge_set.setdefault(output_path, []).append(step_output_path)
	return merge_set
