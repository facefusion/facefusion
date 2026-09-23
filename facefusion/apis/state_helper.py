from facefusion.common_helper import cast_bool, cast_float, cast_int
from facefusion.types import State, StateKey, StateValue


def validate_argument_value(key : StateKey, value : StateValue) -> bool:
	if State.__annotations__.get(key) is int:
		return isinstance(value, int)

	if State.__annotations__.get(key) is float:
		return isinstance(value, float)

	if State.__annotations__.get(key) is bool:
		return isinstance(value, bool)

	if State.__annotations__.get(key) is list:
		return isinstance(value, list)

	return True


def cast_argument_value(key : StateKey, value : StateValue) -> StateValue:
	if State.__annotations__.get(key) is int:
		return cast_int(value)

	if State.__annotations__.get(key) is float:
		return cast_float(value)

	if State.__annotations__.get(key) is bool:
		return cast_bool(value)

	return value
