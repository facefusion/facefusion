from typing import Optional

import gradio

import facefusion.choices
from facefusion import state_manager, voice_extractor, wording
from facefusion.types import VoiceExtractorModel
from facefusion.uis.core import register_ui_component

VOICE_EXTRACTOR_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None


def render() -> None:
	global VOICE_EXTRACTOR_MODEL_DROPDOWN

	VOICE_EXTRACTOR_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.voice_extractor_model_dropdown'),
		choices = facefusion.choices.voice_extractor_models,
		value = state_manager.get_item('voice_extractor_model')
	)
	register_ui_component('voice_extractor_model_dropdown', VOICE_EXTRACTOR_MODEL_DROPDOWN)


def listen() -> None:
	VOICE_EXTRACTOR_MODEL_DROPDOWN.change(update_voice_extractor_model, inputs = VOICE_EXTRACTOR_MODEL_DROPDOWN, outputs = VOICE_EXTRACTOR_MODEL_DROPDOWN)


def update_voice_extractor_model(voice_extractor_model : VoiceExtractorModel) -> gradio.Dropdown:
	voice_extractor.clear_inference_pool()
	state_manager.set_item('voice_extractor_model', voice_extractor_model)

	if voice_extractor.pre_check():
		gradio.Dropdown(value = state_manager.get_item('voice_extractor_model'))
	return gradio.Dropdown()
