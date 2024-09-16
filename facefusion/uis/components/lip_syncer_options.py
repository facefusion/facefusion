from typing import List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.typing import LipSyncerModel
from facefusion.uis.core import get_ui_component, register_ui_component

LIP_SYNCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global LIP_SYNCER_MODEL_DROPDOWN

	LIP_SYNCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.lip_syncer_model_dropdown'),
		choices = processors_choices.lip_syncer_models,
		value = state_manager.get_item('lip_syncer_model'),
		visible = 'lip_syncer' in state_manager.get_item('processors')
	)
	register_ui_component('lip_syncer_model_dropdown', LIP_SYNCER_MODEL_DROPDOWN)


def listen() -> None:
	LIP_SYNCER_MODEL_DROPDOWN.change(update_lip_syncer_model, inputs = LIP_SYNCER_MODEL_DROPDOWN, outputs = LIP_SYNCER_MODEL_DROPDOWN)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = LIP_SYNCER_MODEL_DROPDOWN)


def remote_update(processors : List[str]) -> gradio.Dropdown:
	has_lip_syncer = 'lip_syncer' in processors
	return gradio.Dropdown(visible = has_lip_syncer)


def update_lip_syncer_model(lip_syncer_model : LipSyncerModel) -> gradio.Dropdown:
	lip_syncer_module = load_processor_module('lip_syncer')
	lip_syncer_module.clear_inference_pool()
	state_manager.set_item('lip_syncer_model', lip_syncer_model)

	if lip_syncer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('lip_syncer_model'))
	return gradio.Dropdown()
