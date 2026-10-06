import pytest

from facefusion.apis.job_validator import validate_status


@pytest.mark.parametrize('job_status, expected',
[
	('drafted', True),
	('queued', True),
	('completed', True),
	('failed', True),
	('invalid', False)
])
def test_validate_status(job_status : str, expected : bool) -> None:
	assert validate_status(job_status) is expected
