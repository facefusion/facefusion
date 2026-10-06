import facefusion.choices
from facefusion.types import JobStatus


def validate_status(job_status : JobStatus) -> bool:
	return job_status in facefusion.choices.job_statuses
