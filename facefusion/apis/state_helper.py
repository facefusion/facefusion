from facefusion.common_helper import cast_bool, cast_float, cast_int
from facefusion.normalizer import normalize_color, normalize_space
from facefusion.processors.types import ProcessorState
from facefusion.types import State, StateKey, StateValue


def normalize_argument_value(key : StateKey, value : StateValue) -> StateValue:
	argument_type = (State.__annotations__ | ProcessorState.__annotations__).get(key)

	if argument_type is int:
		return cast_int(value)

	if argument_type is float:
		return cast_float(value)

	if argument_type is bool:
		return cast_bool(value)

	if key in [ 'background_remover_fill_color', 'background_remover_despill_color' ]:
		return normalize_color(value)

	if key in [ 'face_detector_margin', 'face_mask_padding' ]:
		return normalize_space(value)

	return value
