from datetime import datetime
from typing import Optional, Tuple

from facefusion.date_helper import describe_time_ago
from facefusion.jobs import job_manager
from facefusion.types import JobStatus, TableContents, TableHeaders


def compose_job_list(job_status : JobStatus) -> Tuple[TableHeaders, TableContents]:
	jobs = job_manager.find_jobs(job_status)
	job_headers : TableHeaders = [ 'job id', 'steps', 'date created', 'date updated', 'job status' ]
	job_contents : TableContents = []

	for index, job_id in enumerate(jobs):
		if job_manager.validate_job(job_id):
			job = jobs[job_id]
			step_total = job_manager.count_step_total(job_id)
			date_created = prepare_describe_datetime(job.get('date_created'))
			date_updated = prepare_describe_datetime(job.get('date_updated'))
			job_contents.append(
			[
				job_id,
				step_total,
				date_created,
				date_updated,
				job_status
			])
	return job_headers, job_contents


def prepare_describe_datetime(date_time : Optional[str]) -> Optional[str]:
	if date_time:
		return describe_time_ago(datetime.fromisoformat(date_time))
	return None
