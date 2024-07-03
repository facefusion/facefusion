from typing import List, Optional
import gradio

from facefusion.typing import ExecutionProviderKey
from facefusion import state_manager, wording
from facefusion.face_analyser import clear_face_analyser
from facefusion.processors.frame.core import clear_frame_processors_modules
from facefusion.execution import get_execution_provider_choices

EXECUTION_PROVIDERS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global EXECUTION_PROVIDERS_CHECKBOX_GROUP

	EXECUTION_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.execution_providers_checkbox_group'),
		choices = get_execution_provider_choices(),
		value = state_manager.get_item('execution_providers')
	)


def listen() -> None:
	EXECUTION_PROVIDERS_CHECKBOX_GROUP.change(update_execution_providers, inputs = EXECUTION_PROVIDERS_CHECKBOX_GROUP, outputs = EXECUTION_PROVIDERS_CHECKBOX_GROUP)


def update_execution_providers(execution_providers : List[ExecutionProviderKey]) -> gradio.CheckboxGroup:
	clear_face_analyser()
	clear_frame_processors_modules()
	execution_providers = execution_providers or get_execution_provider_choices()
	state_manager.set_item('execution_providers', execution_providers)
	return gradio.CheckboxGroup(value = state_manager.get_item('execution_providers'))
