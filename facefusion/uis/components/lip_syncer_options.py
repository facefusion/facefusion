from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step
from facefusion.processors import choices as processors_choices
from facefusion.processors.core import load_processor_module
from facefusion.processors.types import LipSyncerModel
from facefusion.uis.core import get_ui_component, register_ui_component

LIP_SYNCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
LIP_SYNCER_WEIGHT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global LIP_SYNCER_MODEL_DROPDOWN
	global LIP_SYNCER_WEIGHT_SLIDER

	has_lip_syncer = 'lip_syncer' in state_manager.get_item('processors')
	LIP_SYNCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.lip_syncer_model_dropdown'),
		choices = processors_choices.lip_syncer_models,
		value = state_manager.get_item('lip_syncer_model'),
		visible = has_lip_syncer
	)
	LIP_SYNCER_WEIGHT_SLIDER = gradio.Slider(
		label = wording.get('uis.lip_syncer_weight_slider'),
		value = state_manager.get_item('lip_syncer_weight'),
		step = calc_float_step(processors_choices.lip_syncer_weight_range),
		minimum = processors_choices.lip_syncer_weight_range[0],
		maximum = processors_choices.lip_syncer_weight_range[-1],
		visible = has_lip_syncer
	)
	register_ui_component('lip_syncer_model_dropdown', LIP_SYNCER_MODEL_DROPDOWN)
	register_ui_component('lip_syncer_weight_slider', LIP_SYNCER_WEIGHT_SLIDER)


def listen() -> None:
	LIP_SYNCER_MODEL_DROPDOWN.change(update_lip_syncer_model, inputs = LIP_SYNCER_MODEL_DROPDOWN, outputs = LIP_SYNCER_MODEL_DROPDOWN)
	LIP_SYNCER_WEIGHT_SLIDER.release(update_lip_syncer_weight, inputs = LIP_SYNCER_WEIGHT_SLIDER)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ LIP_SYNCER_MODEL_DROPDOWN, LIP_SYNCER_WEIGHT_SLIDER ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Slider]:
	has_lip_syncer = 'lip_syncer' in processors
	return gradio.Dropdown(visible = has_lip_syncer), gradio.Slider(visible = has_lip_syncer)


def update_lip_syncer_model(lip_syncer_model : LipSyncerModel) -> gradio.Dropdown:
	lip_syncer_module = load_processor_module('lip_syncer')
	lip_syncer_module.clear_inference_pool()
	state_manager.set_item('lip_syncer_model', lip_syncer_model)

	if lip_syncer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('lip_syncer_model'))
	return gradio.Dropdown()


def update_lip_syncer_weight(lip_syncer_weight : float) -> None:
	state_manager.set_item('lip_syncer_weight', lip_syncer_weight)
