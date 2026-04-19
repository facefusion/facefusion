import hashlib
from typing import Any, Sequence

from facefusion.common_helper import cast_int


def sanitize_job_id(job_id : str) -> str:
	__job_id__ = job_id.replace('-', '')

	if __job_id__.isalnum():
		return job_id
	return hashlib.sha1(job_id.encode()).hexdigest()


def sanitize_int_range(value : Any, int_range : Sequence[int]) -> int:
	value = cast_int(value)

	if value in int_range:
		return value
	return int_range[0]
