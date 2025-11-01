from typing import Optional

import gradio

from facefusion import state_manager, translator
from facefusion.filesystem import is_video
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import get_ui_components, register_ui_component
from facefusion.uis.types import ComponentOptions
from facefusion.vision import count_video_frame_total

PREVIEW_FRAME_SLIDER: Optional[gradio.Slider] = None
PREVIEW_MODE_DROPDOWN: Optional[gradio.Dropdown] = None
PREVIEW_RESOLUTION_DROPDOWN: Optional[gradio.Dropdown] = None


def render() -> None:
	global PREVIEW_FRAME_SLIDER, PREVIEW_MODE_DROPDOWN, PREVIEW_RESOLUTION_DROPDOWN

	preview_frame_slider_options : ComponentOptions =\
	{
		'label': translator.get('uis.preview_frame_slider'),
		'step': 1,
		'minimum': 0,
		'maximum': 100,
		'visible': False
	}
	if is_video(state_manager.get_item('target_path')):
		preview_frame_slider_options['value'] = state_manager.get_item('reference_frame_number')
		preview_frame_slider_options['maximum'] = count_video_frame_total(state_manager.get_item('target_path'))
		preview_frame_slider_options['visible'] = True
	PREVIEW_FRAME_SLIDER = gradio.Slider(**preview_frame_slider_options)
	with gradio.Row():
		PREVIEW_MODE_DROPDOWN = gradio.Dropdown(
			label = translator.get('uis.preview_mode_dropdown'),
			value = uis_choices.preview_modes[0],
			choices = uis_choices.preview_modes,
			visible = True
		)
		PREVIEW_RESOLUTION_DROPDOWN = gradio.Dropdown(
			label = translator.get('uis.preview_resolution_dropdown'),
			value = uis_choices.preview_resolutions[-1],
			choices = uis_choices.preview_resolutions,
			visible = True
		)
	register_ui_component('preview_mode_dropdown', PREVIEW_MODE_DROPDOWN)
	register_ui_component('preview_resolution_dropdown', PREVIEW_RESOLUTION_DROPDOWN)
	register_ui_component('preview_frame_slider', PREVIEW_FRAME_SLIDER)


def listen() -> None:
	for ui_component in get_ui_components([ 'target_image', 'target_video' ]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_frame_slider, outputs = PREVIEW_FRAME_SLIDER)


def update_preview_frame_slider() -> gradio.Slider:
	if is_video(state_manager.get_item('target_path')):
		video_frame_total = count_video_frame_total(state_manager.get_item('target_path'))
		return gradio.Slider(maximum = video_frame_total, visible = True)
	return gradio.Slider(value = 0, visible = False)
