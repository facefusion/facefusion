import os
from typing import Tuple
from datetime import datetime

from facefusion.typing import JobStatus, TableHeaders, TableContents
from facefusion.date_helper import describe_time_ago
from facefusion.jobs import job_manager


def get_step_output_path(job_id : str, step_index : int, output_path : str) -> str:
	output_directory_path, file_name_with_extension = os.path.split(output_path)
	output_file_name, output_file_extension = os.path.splitext(file_name_with_extension)
	return os.path.join(output_directory_path, output_file_name + '-' + job_id + '-' + str(step_index) + output_file_extension)


def suggest_job_id(job_prefix : str = 'job') -> str:
	return job_prefix + '-' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def compose_job_list(job_status : JobStatus) -> Tuple[TableHeaders, TableContents]:
	jobs = job_manager.find_jobs(job_status)
	job_headers = [ 'job id', 'steps', 'date created', 'date updated', 'job status' ]
	job_contents = []

	for index, job_id in enumerate(jobs):
		job = jobs[job_id]
		step_total = job_manager.count_step_total(job_id)
		date_created = datetime.fromisoformat(job.get('date_created'))
		date_updated = datetime.fromisoformat(job.get('date_updated'))
		job_contents.append(
		[
			job_id,
			step_total,
			describe_time_ago(date_created),
			describe_time_ago(date_updated),
			job_status
		])
	return job_headers, job_contents
