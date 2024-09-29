from argparse import ArgumentParser, _ArgumentGroup, _SubParsersAction
from typing import List, Optional

import facefusion.choices
from facefusion.processors import choices as processors_choices


def find_argument_group(program : ArgumentParser, group_name : str) -> Optional[_ArgumentGroup]:
	for group in program._action_groups:
		if group.title == group_name:
			return group
	return None


def validate_args(program : ArgumentParser) -> bool:
	if validate_actions(program):
		for action in program._actions:
			if isinstance(action, _SubParsersAction):
				for _, sub_program in action._name_parser_map.items():
					if not validate_args(sub_program):
						return False
		return True
	return False


def validate_actions(program : ArgumentParser) -> bool:
	for action in program._actions:
		if action.default and action.choices:
			if isinstance(action.default, list):
				if any(default not in action.choices for default in action.default):
					return False
			elif action.default not in action.choices:
				return False
	return True


def remove_args(program : ArgumentParser, remove_names : List[str]) -> ArgumentParser:
	actions = [ action for action in program._actions if action.dest in remove_names ]

	for action in actions:
		program._actions.remove(action)
	return program


def suggest_face_detector_choices(program : ArgumentParser) -> List[str]:
	known_args, _ = program.parse_known_args()
	return facefusion.choices.face_detector_set.get(known_args.face_detector_model) #type:ignore[call-overload]


def suggest_face_swapper_pixel_boost_choices(program : ArgumentParser) -> List[str]:
	known_args, _ = program.parse_known_args()
	return processors_choices.face_swapper_set.get(known_args.face_swapper_model) #type:ignore[call-overload]
