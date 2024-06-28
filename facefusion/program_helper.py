from argparse import ArgumentParser, Action, _ArgumentGroup
from copy import copy
from typing import List, Optional
from types import ModuleType

import facefusion.choices
from facefusion.typing import Args
from facefusion.processors.frame import choices as frame_processors_choices


def find_argument_group(program : ArgumentParser, group_name : str) -> Optional[_ArgumentGroup]:
	for group in program._action_groups:
		if group.title == group_name:
			return group
	return None


def validate_args(program : ArgumentParser) -> bool:
	for action in program._actions:
		if action.default and action.choices:
			if isinstance(action.default, list):
				if any(default not in action.choices for default in action.default):
					return False
			elif action.default not in action.choices:
				return False
	return True


def reduce_args(program : ArgumentParser, keys : List[str]) -> ArgumentParser:
	program = copy(program)
	actions : List[Action] = []

	for action in program._actions:
		if action.dest in keys:
			actions.append(action)
	program._actions = actions
	return program


def update_args(program : ArgumentParser, args : Args) -> ArgumentParser:
	program = copy(program)

	for action in program._actions:
		if action.dest in args:
			if action.dest == 'face_detector_size':
				action.choices = suggest_face_detector_choices(program)
			if action.dest == 'face_swapper_pixel_boost':
				action.choices = suggest_face_swapper_pixel_boost_choices(program)
			action.default = args[action.dest]
	return program


def import_globals(program : ArgumentParser, keys : List[str], modules : List[ModuleType]) -> ArgumentParser:
	program = copy(program)
	args : Args = {}

	for module in modules:
		for key in keys:
			if hasattr(module.globals, key):
				args[key] = getattr(module.globals, key)

	if args:
		return update_args(program, args)
	return program


def suggest_face_detector_choices(program : ArgumentParser) -> List[str]:
	known_args, _ = program.parse_known_args()
	return facefusion.choices.face_detector_set.get(known_args.face_detector_model)  # type:ignore[call-overload]


def suggest_face_swapper_pixel_boost_choices(program : ArgumentParser) -> List[str]:
	known_args, _ = program.parse_known_args()
	return frame_processors_choices.face_swapper_set.get(known_args.face_swapper_model)  # type:ignore[call-overload]
