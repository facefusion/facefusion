from typing import cast

import pytest

from facefusion.apis.job_validator import validate_status
from facefusion.types import JobStatus


@pytest.mark.parametrize('job_status, expected',
[
	('drafted', True),
	('queued', True),
	('completed', True),
	('failed', True),
	('invalid', False)
])
def test_validate_status(job_status : str, expected : bool) -> None:
	assert validate_status(cast(JobStatus, job_status)) is expected
