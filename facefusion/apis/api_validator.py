from facefusion.types import Body


def validate_body(body : Body) -> bool:
	return isinstance(body, dict)
