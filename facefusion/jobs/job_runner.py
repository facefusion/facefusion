from facefusion.ffmpeg import concat_video
from facefusion.filesystem import are_images, are_videos, move_file, remove_file
from facefusion.jobs import job_helper, job_manager
from facefusion.types import JobOutputSet, JobStep, ProcessStep


def run_job(job_id : str, process_step : ProcessStep) -> bool:
	queued_job_ids = job_manager.find_job_ids('queued')

	if job_id in queued_job_ids:
		if run_steps(job_id, process_step) and finalize_steps(job_id):
			clean_steps(job_id)
			return job_manager.move_job_file(job_id, 'completed')
		clean_steps(job_id)
		job_manager.move_job_file(job_id, 'failed')
	return False


def run_jobs(process_step : ProcessStep, halt_on_error : bool) -> bool:
	queued_job_ids = job_manager.find_job_ids('queued')
	has_error = False

	if queued_job_ids:
		for job_id in queued_job_ids:
			if not run_job(job_id, process_step):
				has_error = True
				if halt_on_error:
					return False
		return not has_error
	return False


def retry_job(job_id : str, process_step : ProcessStep) -> bool:
	failed_job_ids = job_manager.find_job_ids('failed')

	if job_id in failed_job_ids:
		return job_manager.set_steps_status(job_id, 'queued') and job_manager.move_job_file(job_id, 'queued') and run_job(job_id, process_step)
	return False


def retry_jobs(process_step : ProcessStep, halt_on_error : bool) -> bool:
	failed_job_ids = job_manager.find_job_ids('failed')
	has_error = False

	if failed_job_ids:
		for job_id in failed_job_ids:
			if not retry_job(job_id, process_step):
				has_error = True
				if halt_on_error:
					return False
		return not has_error
	return False


def run_step(job_id : str, step_index : int, step : JobStep, process_step : ProcessStep) -> bool:
	step_args = step.get('args')

	if job_manager.set_step_status(job_id, step_index, 'started') and process_step(job_id, step_index, step_args):
		output_path = step_args.get('output_path')
		step_output_path = job_helper.get_step_output_path(job_id, step_index, output_path)

		return move_file(output_path, step_output_path) and job_manager.set_step_status(job_id, step_index, 'completed')
	job_manager.set_step_status(job_id, step_index, 'failed')
	return False


def run_steps(job_id : str, process_step : ProcessStep) -> bool:
	steps = job_manager.get_steps(job_id)

	if steps:
		for index, step in enumerate(steps):
			if not run_step(job_id, index, step, process_step):
				return False
		return True
	return False


def finalize_steps(job_id : str) -> bool:
	output_set = collect_output_set(job_id)

	for output_path, temp_output_paths in output_set.items():
		if are_videos(temp_output_paths):
			if not concat_video(output_path, temp_output_paths):
				return False
		if are_images(temp_output_paths):
			for temp_output_path in temp_output_paths:
				if not move_file(temp_output_path, output_path):
					return False
	return True


def clean_steps(job_id: str) -> bool:
	output_set = collect_output_set(job_id)

	for temp_output_paths in output_set.values():
		for temp_output_path in temp_output_paths:
			if not remove_file(temp_output_path):
				return False
	return True


def collect_output_set(job_id : str) -> JobOutputSet:
	steps = job_manager.get_steps(job_id)
	job_output_set : JobOutputSet = {}

	for index, step in enumerate(steps):
		output_path = step.get('args').get('output_path')

		if output_path:
			step_output_path = job_manager.get_step_output_path(job_id, index, output_path)
			job_output_set.setdefault(output_path, []).append(step_output_path)
	return job_output_set
