from typing import Any, Literal, get_origin

from facefusion import capability_store
from facefusion.processors.types import ProcessorState
from facefusion.types import State, StateKey, StateValue


def validate_argument_key(key : StateKey) -> bool:
	return key in capability_store.get_api_arguments()


def validate_argument_value(key : StateKey, value : StateValue) -> bool:
	argument_type = (State.__annotations__ | ProcessorState.__annotations__).get(key)
	choices = capability_store.get_api_capability_set().get(key).get('choices')

	if argument_type in [ int, float, str ]:
		if choices:
			return isinstance(value, argument_type) and value in choices

		return isinstance(value, argument_type)

	if get_origin(argument_type) is list:
		if choices:
			return isinstance(value, list) and all(choice in choices for choice in value)

		return isinstance(value, list)

	if get_origin(argument_type) is tuple:
		return isinstance(value, tuple)

	if get_origin(argument_type) is Literal:
		if choices:
			return isinstance(value, str) and value in choices

		return isinstance(value, str)

	return True


def validate_face_selector_maps(face_selector_maps : Any) -> bool:
	if isinstance(face_selector_maps, list):
		for face_selector_map in face_selector_maps:
			source_faces = face_selector_map.get('source_faces')
			reference_faces = face_selector_map.get('reference_faces')

			if not validate_face_pointers(source_faces) or not validate_face_pointers(reference_faces):
				return False

		return True

	return False


def validate_face_pointers(face_pointers : Any) -> bool:
	if isinstance(face_pointers, list):
		for face_pointer in face_pointers:
			frame_index = face_pointer.get('frame_index')
			face_position = face_pointer.get('face_position')

			if not isinstance(frame_index, int) or not isinstance(face_position, int):
				return False

			if frame_index < 0 or face_position < 0:
				return False

		return True

	return False
