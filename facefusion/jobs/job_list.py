from datetime import datetime
from typing import Tuple

from facefusion.date_helper import describe_time_ago
from facefusion.jobs import job_manager
from facefusion.typing import JobStatus, TableContents, TableHeaders


def compose_job_list(job_status : JobStatus) -> Tuple[TableHeaders, TableContents]:
	jobs = job_manager.find_jobs(job_status)
	job_headers : TableHeaders = [ 'job id', 'steps', 'date created', 'date updated', 'job status' ]
	job_contents : TableContents = []

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
