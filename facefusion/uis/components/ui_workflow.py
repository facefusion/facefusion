from typing import Optional

import gradio

import facefusion
from facefusion import state_manager, wording
from facefusion.typing import UiWorkflow
from facefusion.uis.core import register_ui_component

UI_WORKFLOW_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global UI_WORKFLOW_DROPDOWN

	UI_WORKFLOW_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.ui_workflow'),
		choices = facefusion.choices.ui_workflows,
		value = state_manager.get_item('ui_workflow')
	)


def listen() -> None:
	UI_WORKFLOW_DROPDOWN.change(update_ui_workflow, inputs = UI_WORKFLOW_DROPDOWN)
	register_ui_component('ui_workflow_dropdown', UI_WORKFLOW_DROPDOWN)


def update_ui_workflow(ui_workflow : UiWorkflow) -> None:
	state_manager.set_item('ui_workflow', ui_workflow)
