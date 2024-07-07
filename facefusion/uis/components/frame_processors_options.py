from typing import List, Optional, Tuple

import gradio

from facefusion import face_analyser, state_manager, wording
from facefusion.common_helper import get_first
from facefusion.processors.frame import choices as frame_processors_choices
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.processors.frame.typing import FaceDebuggerItem, FaceEnhancerModel, FaceSwapperModel, FrameColorizerModel, FrameEnhancerModel, LipSyncerModel, AgeModifierModel
from facefusion.uis.core import get_ui_component, register_ui_component

FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
FACE_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None
FACE_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SWAPPER_PIXEL_BOOST_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_COLORIZER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_COLORIZER_BLEND_SLIDER : Optional[gradio.Slider] = None
FRAME_COLORIZER_SIZE_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_ENHANCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
FRAME_ENHANCER_BLEND_SLIDER : Optional[gradio.Slider] = None
LIP_SYNCER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
AGE_MODIFIER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
AGE_MODIFIER_DIRECTION_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP
	global FACE_ENHANCER_MODEL_DROPDOWN
	global FACE_ENHANCER_BLEND_SLIDER
	global FACE_SWAPPER_MODEL_DROPDOWN
	global FACE_SWAPPER_PIXEL_BOOST_DROPDOWN
	global FRAME_COLORIZER_MODEL_DROPDOWN
	global FRAME_COLORIZER_BLEND_SLIDER
	global FRAME_COLORIZER_SIZE_DROPDOWN
	global FRAME_ENHANCER_MODEL_DROPDOWN
	global FRAME_ENHANCER_BLEND_SLIDER
	global LIP_SYNCER_MODEL_DROPDOWN
	global AGE_MODIFIER_MODEL_DROPDOWN
	global AGE_MODIFIER_DIRECTION_SLIDER

	FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.face_debugger_items_checkbox_group'),
		choices = frame_processors_choices.face_debugger_items,
		value = state_manager.get_item('face_debugger_items'),
		visible = 'face_debugger' in state_manager.get_item('frame_processors')
	)
	FACE_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_enhancer_model_dropdown'),
		choices = frame_processors_choices.face_enhancer_models,
		value = state_manager.get_item('face_enhancer_model'),
		visible = 'face_enhancer' in state_manager.get_item('frame_processors')
	)
	FACE_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.face_enhancer_blend_slider'),
		value = state_manager.get_item('face_enhancer_blend'),
		step = frame_processors_choices.face_enhancer_blend_range[1] - frame_processors_choices.face_enhancer_blend_range[0],
		minimum = frame_processors_choices.face_enhancer_blend_range[0],
		maximum = frame_processors_choices.face_enhancer_blend_range[-1],
		visible = 'face_enhancer' in state_manager.get_item('frame_processors')
	)
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
	FRAME_COLORIZER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.frame_colorizer_model_dropdown'),
		choices = frame_processors_choices.frame_colorizer_models,
		value = state_manager.get_item('frame_colorizer_model'),
		visible = 'frame_colorizer' in state_manager.get_item('frame_processors')
	)
	FRAME_COLORIZER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.frame_colorizer_blend_slider'),
		value = state_manager.get_item('frame_colorizer_blend'),
		step = frame_processors_choices.frame_colorizer_blend_range[1] - frame_processors_choices.frame_colorizer_blend_range[0],
		minimum = frame_processors_choices.frame_colorizer_blend_range[0],
		maximum = frame_processors_choices.frame_colorizer_blend_range[-1],
		visible = 'frame_colorizer' in state_manager.get_item('frame_processors')
	)
	FRAME_COLORIZER_SIZE_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.frame_colorizer_size_dropdown'),
		choices = frame_processors_choices.frame_colorizer_sizes,
		value = state_manager.get_item('frame_colorizer_size'),
		visible = 'frame_colorizer' in state_manager.get_item('frame_processors')
	)
	FRAME_ENHANCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.frame_enhancer_model_dropdown'),
		choices = frame_processors_choices.frame_enhancer_models,
		value = state_manager.get_item('frame_enhancer_model'),
		visible = 'frame_enhancer' in state_manager.get_item('frame_processors')
	)
	FRAME_ENHANCER_BLEND_SLIDER = gradio.Slider(
		label = wording.get('uis.frame_enhancer_blend_slider'),
		value = state_manager.get_item('frame_enhancer_blend'),
		step = frame_processors_choices.frame_enhancer_blend_range[1] - frame_processors_choices.frame_enhancer_blend_range[0],
		minimum = frame_processors_choices.frame_enhancer_blend_range[0],
		maximum = frame_processors_choices.frame_enhancer_blend_range[-1],
		visible = 'frame_enhancer' in state_manager.get_item('frame_processors')
	)
	LIP_SYNCER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.lip_syncer_model_dropdown'),
		choices = frame_processors_choices.lip_syncer_models,
		value = state_manager.get_item('lip_syncer_model'),
		visible = 'lip_syncer' in state_manager.get_item('frame_processors')
	)
	AGE_MODIFIER_MODEL_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.age_modifier_model_dropdown'),
		choices = frame_processors_choices.age_modifier_models,
		value = state_manager.get_item('age_modifier_model'),
		visible = 'age_modifier' in state_manager.get_item('frame_processors')
	)
	AGE_MODIFIER_DIRECTION_SLIDER = gradio.Slider(
		label = wording.get('uis.age_modifier_direction_slider'),
		value = state_manager.get_item('age_modifier_direction'),
		step = frame_processors_choices.age_modifier_direction_range[1] - frame_processors_choices.age_modifier_direction_range[0],
		minimum = frame_processors_choices.age_modifier_direction_range[0],
		maximum = frame_processors_choices.age_modifier_direction_range[-1],
		visible = 'age_modifier' in state_manager.get_item('frame_processors')
	)
	register_ui_component('face_debugger_items_checkbox_group', FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP)
	register_ui_component('face_enhancer_model_dropdown', FACE_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('face_enhancer_blend_slider', FACE_ENHANCER_BLEND_SLIDER)
	register_ui_component('face_swapper_model_dropdown', FACE_SWAPPER_MODEL_DROPDOWN)
	register_ui_component('face_swapper_pixel_boost_dropdown', FACE_SWAPPER_PIXEL_BOOST_DROPDOWN)
	register_ui_component('frame_colorizer_model_dropdown', FRAME_COLORIZER_MODEL_DROPDOWN)
	register_ui_component('frame_colorizer_blend_slider', FRAME_COLORIZER_BLEND_SLIDER)
	register_ui_component('frame_colorizer_size_dropdown', FRAME_COLORIZER_SIZE_DROPDOWN)
	register_ui_component('frame_enhancer_model_dropdown', FRAME_ENHANCER_MODEL_DROPDOWN)
	register_ui_component('frame_enhancer_blend_slider', FRAME_ENHANCER_BLEND_SLIDER)
	register_ui_component('lip_syncer_model_dropdown', LIP_SYNCER_MODEL_DROPDOWN)
	register_ui_component('age_modifier_model_dropdown', AGE_MODIFIER_MODEL_DROPDOWN)
	register_ui_component('age_modifier_direction_slider', AGE_MODIFIER_DIRECTION_SLIDER)


def listen() -> None:
	FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP.change(update_face_debugger_items, inputs = FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP)
	FACE_ENHANCER_MODEL_DROPDOWN.change(update_face_enhancer_model, inputs = FACE_ENHANCER_MODEL_DROPDOWN, outputs = FACE_ENHANCER_MODEL_DROPDOWN)
	FACE_ENHANCER_BLEND_SLIDER.release(update_face_enhancer_blend, inputs = FACE_ENHANCER_BLEND_SLIDER)
	FACE_SWAPPER_MODEL_DROPDOWN.change(update_face_swapper_model, inputs = FACE_SWAPPER_MODEL_DROPDOWN, outputs = [ FACE_SWAPPER_MODEL_DROPDOWN, FACE_SWAPPER_PIXEL_BOOST_DROPDOWN ])
	FACE_SWAPPER_PIXEL_BOOST_DROPDOWN.change(update_face_swapper_pixel_boost, inputs = FACE_SWAPPER_PIXEL_BOOST_DROPDOWN)
	FRAME_COLORIZER_MODEL_DROPDOWN.change(update_frame_colorizer_model, inputs = FRAME_COLORIZER_MODEL_DROPDOWN, outputs = FRAME_COLORIZER_MODEL_DROPDOWN)
	FRAME_COLORIZER_BLEND_SLIDER.release(update_frame_colorizer_blend, inputs = FRAME_COLORIZER_BLEND_SLIDER)
	FRAME_COLORIZER_SIZE_DROPDOWN.change(update_frame_colorizer_size, inputs = FRAME_COLORIZER_SIZE_DROPDOWN)
	FRAME_ENHANCER_MODEL_DROPDOWN.change(update_frame_enhancer_model, inputs = FRAME_ENHANCER_MODEL_DROPDOWN, outputs = FRAME_ENHANCER_MODEL_DROPDOWN)
	FRAME_ENHANCER_BLEND_SLIDER.release(update_frame_enhancer_blend, inputs = FRAME_ENHANCER_BLEND_SLIDER)
	LIP_SYNCER_MODEL_DROPDOWN.change(update_lip_syncer_model, inputs = LIP_SYNCER_MODEL_DROPDOWN, outputs = LIP_SYNCER_MODEL_DROPDOWN)
	AGE_MODIFIER_MODEL_DROPDOWN.change(update_age_modifier_model, inputs = AGE_MODIFIER_MODEL_DROPDOWN, outputs = AGE_MODIFIER_MODEL_DROPDOWN)
	AGE_MODIFIER_DIRECTION_SLIDER.release(update_age_modifier_direction, inputs = AGE_MODIFIER_DIRECTION_SLIDER)
	frame_processors_checkbox_group = get_ui_component('frame_processors_checkbox_group')
	if frame_processors_checkbox_group:
		frame_processors_checkbox_group.change(update_frame_processors, inputs = frame_processors_checkbox_group, outputs = [ FACE_DEBUGGER_ITEMS_CHECKBOX_GROUP, FACE_ENHANCER_MODEL_DROPDOWN, FACE_ENHANCER_BLEND_SLIDER, FACE_SWAPPER_MODEL_DROPDOWN, FACE_SWAPPER_PIXEL_BOOST_DROPDOWN, FRAME_COLORIZER_MODEL_DROPDOWN, FRAME_COLORIZER_BLEND_SLIDER, FRAME_COLORIZER_SIZE_DROPDOWN, FRAME_ENHANCER_MODEL_DROPDOWN, FRAME_ENHANCER_BLEND_SLIDER, LIP_SYNCER_MODEL_DROPDOWN, AGE_MODIFIER_MODEL_DROPDOWN, AGE_MODIFIER_DIRECTION_SLIDER ])


def update_frame_processors(frame_processors : List[str]) -> Tuple[gradio.CheckboxGroup, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Slider]:
	has_face_debugger = 'face_debugger' in frame_processors
	has_face_enhancer = 'face_enhancer' in frame_processors
	has_face_swapper = 'face_swapper' in frame_processors
	has_frame_colorizer = 'frame_colorizer' in frame_processors
	has_frame_enhancer = 'frame_enhancer' in frame_processors
	has_lip_syncer = 'lip_syncer' in frame_processors
	has_age_modifier = 'age_modifier' in frame_processors
	return gradio.CheckboxGroup(visible = has_face_debugger), gradio.Dropdown(visible = has_face_enhancer), gradio.Slider(visible = has_face_enhancer), gradio.Dropdown(visible = has_face_swapper), gradio.Dropdown(visible = has_face_swapper), gradio.Dropdown(visible = has_frame_colorizer), gradio.Slider(visible = has_frame_colorizer), gradio.Dropdown(visible = has_frame_colorizer), gradio.Dropdown(visible = has_frame_enhancer), gradio.Slider(visible = has_frame_enhancer), gradio.Dropdown(visible = has_lip_syncer), gradio.Dropdown(visible = has_age_modifier), gradio.Slider(visible = has_age_modifier)


def update_face_debugger_items(face_debugger_items : List[FaceDebuggerItem]) -> None:
	state_manager.set_item('face_debugger_items', face_debugger_items)


def update_face_enhancer_model(face_enhancer_model : FaceEnhancerModel) -> gradio.Dropdown:
	state_manager.set_item('face_enhancer_model', face_enhancer_model)
	face_enhancer_module = load_frame_processor_module('face_enhancer')
	face_enhancer_module.clear_frame_processor()
	face_enhancer_module.set_options('model', face_enhancer_module.MODELS[state_manager.get_item('face_enhancer_model')])
	if face_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('face_enhancer_model'))
	return gradio.Dropdown()


def update_face_enhancer_blend(face_enhancer_blend : float) -> None:
	state_manager.set_item('face_enhancer_blend', int(face_enhancer_blend))


def update_face_swapper_model(face_swapper_model : FaceSwapperModel) -> Tuple[gradio.Dropdown, gradio.Dropdown]:
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
	face_swapper_module = load_frame_processor_module('face_swapper')
	face_swapper_module.clear_model_initializer()
	face_swapper_module.clear_frame_processor()
	face_swapper_module.set_options('model', face_swapper_module.MODELS[state_manager.get_item('face_swapper_model')])
	if face_analyser.pre_check() and face_swapper_module.pre_check():
		face_swapper_pixel_boost_choices = frame_processors_choices.face_swapper_set.get(state_manager.get_item('face_swapper_model'))
		return gradio.Dropdown(value = state_manager.get_item('face_swapper_model')), gradio.Dropdown(choices = face_swapper_pixel_boost_choices, value = get_first(face_swapper_pixel_boost_choices))
	return gradio.Dropdown(), gradio.Dropdown()


def update_face_swapper_pixel_boost(face_swapper_pixel_boost : str) -> None:
	state_manager.set_item('face_swapper_pixel_boost', face_swapper_pixel_boost)


def update_frame_colorizer_model(frame_colorizer_model : FrameColorizerModel) -> gradio.Dropdown:
	state_manager.set_item('frame_colorizer_model', frame_colorizer_model)
	frame_colorizer_module = load_frame_processor_module('frame_colorizer')
	frame_colorizer_module.clear_frame_processor()
	frame_colorizer_module.set_options('model', frame_colorizer_module.MODELS[frame_colorizer_model])
	if frame_colorizer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('frame_colorizer_model'))
	return gradio.Dropdown()


def update_frame_colorizer_blend(frame_colorizer_blend : float) -> None:
	state_manager.set_item('frame_colorizer_blend', int(frame_colorizer_blend))


def update_frame_colorizer_size(frame_colorizer_size : str) -> None:
	state_manager.set_item('frame_colorizer_size', frame_colorizer_size)


def update_frame_enhancer_model(frame_enhancer_model : FrameEnhancerModel) -> gradio.Dropdown:
	state_manager.set_item('frame_enhancer_model', frame_enhancer_model)
	frame_enhancer_module = load_frame_processor_module('frame_enhancer')
	frame_enhancer_module.clear_frame_processor()
	frame_enhancer_module.set_options('model', frame_enhancer_module.MODELS[state_manager.get_item('frame_enhancer_model')])
	if frame_enhancer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('frame_enhancer_model'))
	return gradio.Dropdown()


def update_frame_enhancer_blend(frame_enhancer_blend : float) -> None:
	state_manager.set_item('frame_enhancer_blend', int(frame_enhancer_blend))


def update_lip_syncer_model(lip_syncer_model : LipSyncerModel) -> gradio.Dropdown:
	state_manager.set_item('lip_syncer_model', lip_syncer_model)
	lip_syncer_module = load_frame_processor_module('lip_syncer')
	lip_syncer_module.clear_frame_processor()
	lip_syncer_module.set_options('model', lip_syncer_module.MODELS[state_manager.get_item('lip_syncer_model')])
	if lip_syncer_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('lip_syncer_model'))
	return gradio.Dropdown()


def update_age_modifier_model(age_modifier_model : AgeModifierModel) -> gradio.Dropdown:
	state_manager.set_item('age_modifier_model', age_modifier_model)
	age_modifier_module = load_frame_processor_module('age_modifier')
	age_modifier_module.clear_frame_processor()
	age_modifier_module.set_options('model', age_modifier_module.MODELS[state_manager.get_item('age_modifier_model')])
	if age_modifier_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('age_modifier_model'))
	return gradio.Dropdown()


def update_age_modifier_direction(age_modifier_direction : float) -> None:
	state_manager.set_item('age_modifier_direction', int(age_modifier_direction))
