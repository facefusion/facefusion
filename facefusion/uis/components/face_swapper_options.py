from typing import List, Optional, Tuple

import gradio

from facefusion import face_analyser, state_manager, wording
from facefusion.common_helper import get_first
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame.typing import FaceSwapperModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SWAPPER_PIXEL_BOOST_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_SWAPPER_MODEL_DROPDOWN
	global FACE_SWAPPER_PIXEL_BOOST_DROPDOWN
	global FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER

	FACE_SWAPPER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_swapper_model_dropdown'),
		choices = frame_processors_choices.face_swapper_set.keys(),
		value = state_manager.get_item('face_swapper_model'),
		visible = 'face_swapper' in state_manager.get_item('frame_processors')
	)
	FACE_SWAPPER_PIXEL_BOOST_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_swapper_pixel_boost_dropdown'),
		choices = frame_processors_choices.face_swapper_set.get(state_manager.get_item('face_swapper_model')),
		value = state_manager.get_item('face_swapper_pixel_boost'),
		visible = 'face_swapper' in state_manager.get_item('frame_processors')
	)
	FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER = gradio.Slider(
		label = wording.get('uis.face_swapper_expression_restorer_slider'),
		value = state_manager.get_item('face_swapper_expression_restorer'),
		step = frame_processors_choices.face_swapper_expression_restorer_range[1] - frame_processors_choices.face_swapper_expression_restorer_range[0],
		minimum = frame_processors_choices.face_swapper_expression_restorer_range[0],
		maximum = frame_processors_choices.face_swapper_expression_restorer_range[-1],
		visible = 'face_swapper' in state_manager.get_item('frame_processors')
	)
	register_ui_component('face_swapper_model_dropdown', FACE_SWAPPER_MODEL_DROPDOWN)
	register_ui_component('face_swapper_pixel_boost_dropdown', FACE_SWAPPER_PIXEL_BOOST_DROPDOWN)
	register_ui_component('face_swapper_expression_restorer_slider', FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER)


def listen() -> None:
	FACE_SWAPPER_MODEL_DROPDOWN.change(update_face_swapper_model, inputs = FACE_SWAPPER_MODEL_DROPDOWN, outputs = [ FACE_SWAPPER_MODEL_DROPDOWN, FACE_SWAPPER_PIXEL_BOOST_DROPDOWN ])
	FACE_SWAPPER_PIXEL_BOOST_DROPDOWN.change(update_face_swapper_pixel_boost, inputs = FACE_SWAPPER_PIXEL_BOOST_DROPDOWN)
	FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER.release(update_face_swapper_expression_restorer, inputs = FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER)

	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(remote_update, inputs = frame_processors_checkbox_group, outputs = [ FACE_SWAPPER_MODEL_DROPDOWN, FACE_SWAPPER_PIXEL_BOOST_DROPDOWN, FACE_SWAPPER_EXPRESSION_RESTORER_SLIDER ])


def remote_update(frame_processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Dropdown, gradio.Slider]:
	has_face_swapper = 'face_swapper' in frame_processors
	return gradio.Dropdown(visible = has_face_swapper), gradio.Dropdown(visible = has_face_swapper), gradio.Slider(visible = has_face_swapper)


def update_face_swapper_model(face_swapper_model : FaceSwapperModel) -> Tuple[gradio.Dropdown, gradio.Dropdown]:
	face_swapper_module = load_frame_processor_module('face_swapper')
	face_swapper_module.clear_frame_processor()
	state_manager.set_item('face_swapper_model', face_swapper_model)
	if state_manager.get_item('face_swapper_model') == 'blendswap_256':
		state_manager.set_item('face_recognizer_model', 'arcface_blendswap')
	if state_manager.get_item('face_swapper_model') in [ 'ghost_256_unet_1', 'ghost_256_unet_2', 'ghost_256_unet_3' ]:
		state_manager.set_item('face_recognizer_model', 'arcface_ghost')
	if state_manager.get_item('face_swapper_model') in [ 'inswapper_128', 'inswapper_128_fp16' ]:
		state_manager.set_item('face_recognizer_model', 'arcface_inswapper')
	if state_manager.get_item('face_swapper_model') in [ 'simswap_256', 'simswap_512_unofficial' ]:
		state_manager.set_item('face_recognizer_model', 'arcface_simswap')
	if state_manager.get_item('face_swapper_model') == 'uniface_256':
		state_manager.set_item('face_recognizer_model', 'arcface_uniface')
	face_swapper_module.set_options('model', face_swapper_module.MODELS[state_manager.get_item('face_swapper_model')])

	if face_analyser.pre_check() and face_swapper_module.pre_check():
		face_swapper_pixel_boost_choices = frame_processors_choices.face_swapper_set.get(state_manager.get_item('face_swapper_model'))
		return gradio.Dropdown(value = state_manager.get_item('face_swapper_model')), gradio.Dropdown(choices = face_swapper_pixel_boost_choices, value = get_first(face_swapper_pixel_boost_choices))
	return gradio.Dropdown(), gradio.Dropdown()


def update_face_swapper_pixel_boost(face_swapper_pixel_boost : str) -> None:
	state_manager.set_item('face_swapper_pixel_boost', face_swapper_pixel_boost)


def update_face_swapper_expression_restorer(face_swapper_expression_restorer : float) -> None:
	state_manager.set_item('face_swapper_expression_restorer', face_swapper_expression_restorer)
