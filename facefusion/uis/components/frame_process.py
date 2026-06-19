from typing import Optional

import gradio

import facefusion.choices
from facefusion import state_manager, translator
from facefusion.common_helper import calculate_int_step
from facefusion.uis.core import register_ui_component

TARGET_FRAME_AMOUNT_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global TARGET_FRAME_AMOUNT_SLIDER

	TARGET_FRAME_AMOUNT_SLIDER = gradio.Slider(
		label = translator.get('uis.target_frame_amount_slider'),
		value = state_manager.get_item('target_frame_amount'),
		step = calculate_int_step(facefusion.choices.target_frame_amount_range),
		minimum = facefusion.choices.target_frame_amount_range[0],
		maximum = facefusion.choices.target_frame_amount_range[-1]
	)
	register_ui_component('target_frame_amount_slider', TARGET_FRAME_AMOUNT_SLIDER)


def listen() -> None:
	TARGET_FRAME_AMOUNT_SLIDER.release(update_target_frame_amount, inputs = TARGET_FRAME_AMOUNT_SLIDER)


def update_target_frame_amount(target_frame_amount : float) -> None:
	state_manager.set_item('target_frame_amount', int(target_frame_amount))
