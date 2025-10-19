from typing import Optional

import gradio

import facefusion
from facefusion import state_manager, translator
from facefusion.uis.core import register_ui_component
from facefusion.locals import LOCALS


translator.load(LOCALS, __name__)

UI_WORKFLOW_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global UI_WORKFLOW_DROPDOWN

	UI_WORKFLOW_DROPDOWN = gradio.Dropdown(
		label = translator.get('uis.ui_workflow', __name__),
		choices = facefusion.choices.ui_workflows,
		value = state_manager.get_item('ui_workflow'),
		interactive = True
	)
	register_ui_component('ui_workflow_dropdown', UI_WORKFLOW_DROPDOWN)
