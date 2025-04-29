from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FaceDebuggerItem
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP

	has_face_debugger = 'face_debugger' in state_manager.get_item('processors')
	FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.face_debugger_items_checkbox_group'),
		choices = processors_choices.face_debugger_items,
		value = state_manager.get_item('face_debugger_items'),
		visible = has_face_debugger
	)
	register_ui_component('face_debugger_items_checkbox_group', FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP)


def listen() -> None:
	FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP.change(update_face_debugger_items, inputs = FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP)


def remote_update(processors : List[str]) -> gradio.CheckboxGroup:
	has_face_debugger = 'face_debugger' in processors
	return gradio.CheckboxGroup(visible = has_face_debugger)


def update_face_debugger_items(face_debugger_items : List[FaceDebuggerItem]) -> None:
	state_manager.set_item('face_debugger_items', face_debugger_items)
