from facefusion.apis.api_validator import validate_body


def test_validate_body() -> None:
	assert validate_body({}) is True
	assert validate_body('invalid') is False
