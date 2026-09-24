from typing import get_origin

from facefusion import capability_store
from facefusion.common_helper import cast_bool, cast_float, cast_int
from facefusion.types import State, StateKey, StateValue


def validate_argument_key(key : StateKey) -> bool:
	return key in capability_store.get_api_arguments()


def validate_argument_value(key : StateKey, value : StateValue) -> bool:
	argument_type = State.__annotations__.get(key)
	choices = capability_store.get_api_capability_set().get(key).get('choices')

	if argument_type in [ int, float, str ]:
		if choices:
			return isinstance(value, argument_type) and value in choices

		return isinstance(value, argument_type)

	if get_origin(argument_type) is list:
		if choices:
			return isinstance(value, list) and all(choice in choices for choice in value)

		return isinstance(value, list)

	return True


def cast_argument_value(key : StateKey, value : StateValue) -> StateValue:
	argument_type = State.__annotations__.get(key)

	if argument_type is int:
		return cast_int(value)

	if argument_type is float:
		return cast_float(value)

	if argument_type is bool:
		return cast_bool(value)

	return value
