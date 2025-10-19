from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, register_ui_component, translator


from facefusion.processors.modules.background_remover.locals import LOCALS

translator.load(LOCALS, __name__)

BACKGROUND_REMOVER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None
BACKGROUND_REMOVER_COLOR_RED_NUMBER : Optional[gradio.Number] = None
BACKGROUND_REMOVER_COLOR_GREEN_NUMBER : Optional[gradio.Number] = None
BACKGROUND_REMOVER_COLOR_BLUE_NUMBER : Optional[gradio.Number] = None
BACKGROUND_REMOVER_COLOR_ALPHA_NUMBER : Optional[gradio.Number] = None


def render() -> None:
	global BACKGROUND_REMOVER_MODEL_DROPDOWN
	global BACKGROUND_REMOVER_COLOR_RED_NUMBER
	global BACKGROUND_REMOVER_COLOR_GREEN_NUMBER
	global BACKGROUND_REMOVER_COLOR_BLUE_NUMBER
	global BACKGROUND_REMOVER_COLOR_ALPHA_NUMBER

	has_background_remover = 'background_remover' in state_manager.get_item('processors')
	background_remover_color = state_manager.get_item('background_remover_color')
	BACKGROUND_REMOVER_MODEL_DROPDOWN = gradio.Dropdown(
		label = translator.get('background_remover_uis.model_dropdown', __name__),
		choices = processors_choices.background_remover_models,
		value = state_manager.get_item('background_remover_model'),
		visible = has_background_remover
	)
	with gradio.Group():
		with gradio.Row():
			BACKGROUND_REMOVER_COLOR_RED_NUMBER = gradio.Number(
				label = translator.get('background_remover_uis.color_red_number', __name__),
				value = background_remover_color[0],
				minimum = processors_choices.background_remover_color_range[0],
				maximum = processors_choices.background_remover_color_range[-1],
				step = calculate_int_step(processors_choices.background_remover_color_range),
				visible = has_background_remover,
			)
			BACKGROUND_REMOVER_COLOR_GREEN_NUMBER = gradio.Number(
				label = translator.get('background_remover_uis.color_green_number', __name__),
				value = background_remover_color[1],
				minimum = processors_choices.background_remover_color_range[0],
				maximum = processors_choices.background_remover_color_range[-1],
				step = calculate_int_step(processors_choices.background_remover_color_range),
				visible = has_background_remover,
			)
		with gradio.Row():
			BACKGROUND_REMOVER_COLOR_BLUE_NUMBER = gradio.Number(
				label = translator.get('background_remover_uis.color_blue_number', __name__),
				value = background_remover_color[2],
				minimum = processors_choices.background_remover_color_range[0],
				maximum = processors_choices.background_remover_color_range[-1],
				step = calculate_int_step(processors_choices.background_remover_color_range),
				visible = has_background_remover,
			)
			BACKGROUND_REMOVER_COLOR_ALPHA_NUMBER = gradio.Number(
				label = translator.get('background_remover_uis.color_alpha_number', __name__),
				value = background_remover_color[3],
				minimum = processors_choices.background_remover_color_range[0],
				maximum = processors_choices.background_remover_color_range[-1],
				step = calculate_int_step(processors_choices.background_remover_color_range),
				visible = has_background_remover,
			)
	register_ui_component('background_remover_model_dropdown', BACKGROUND_REMOVER_MODEL_DROPDOWN)
	register_ui_component('background_remover_color_red_number', BACKGROUND_REMOVER_COLOR_RED_NUMBER)
	register_ui_component('background_remover_color_green_number', BACKGROUND_REMOVER_COLOR_GREEN_NUMBER)
	register_ui_component('background_remover_color_blue_number', BACKGROUND_REMOVER_COLOR_BLUE_NUMBER)
	register_ui_component('background_remover_color_alpha_number', BACKGROUND_REMOVER_COLOR_ALPHA_NUMBER)


def listen() -> None:
	BACKGROUND_REMOVER_MODEL_DROPDOWN.change(update_background_remover_model, inputs = BACKGROUND_REMOVER_MODEL_DROPDOWN, outputs = BACKGROUND_REMOVER_MODEL_DROPDOWN)
	background_remover_color_inputs = [BACKGROUND_REMOVER_COLOR_RED_NUMBER, BACKGROUND_REMOVER_COLOR_GREEN_NUMBER, BACKGROUND_REMOVER_COLOR_BLUE_NUMBER, BACKGROUND_REMOVER_COLOR_ALPHA_NUMBER]
	for color_input in background_remover_color_inputs:
		color_input.change(update_background_remover_color, inputs = background_remover_color_inputs)

	processors_checkbox_group = get_ui_component('processors_checkbox_group')
	if processors_checkbox_group:
		processors_checkbox_group.change(remote_update, inputs = processors_checkbox_group, outputs = [ BACKGROUND_REMOVER_MODEL_DROPDOWN, *background_remover_color_inputs ])


def remote_update(processors : List[str]) -> Tuple[gradio.Dropdown, gradio.Number, gradio.Number, gradio.Number, gradio.Number]:
	has_background_remover = 'background_remover' in processors
	return gradio.Dropdown(visible = has_background_remover), gradio.Number(visible = has_background_remover), gradio.Number(visible = has_background_remover), gradio.Number(visible = has_background_remover), gradio.Number(visible = has_background_remover)


def update_background_remover_model(background_remover_model : BackgroundRemoverModel) -> gradio.Dropdown:
	background_remover_module = load_processor_module('background_remover')
	background_remover_module.clear_inference_pool()
	state_manager.set_item('background_remover_model', background_remover_model)

	if background_remover_module.pre_check():
		return gradio.Dropdown(value = state_manager.get_item('background_remover_model'))
	return gradio.Dropdown()


def update_background_remover_color(red : int, green : int, blue : int, alpha : int) -> None:
	red = sanitize_int_range(red, processors_choices.background_remover_color_range)
	green = sanitize_int_range(green, processors_choices.background_remover_color_range)
	blue = sanitize_int_range(blue, processors_choices.background_remover_color_range)
	alpha = sanitize_int_range(alpha, processors_choices.background_remover_color_range)
	state_manager.set_item('background_remover_color', (red, green, blue, alpha))
