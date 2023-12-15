from typing import Optional, Tuple, List
import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.typing import FaceMaskType, FaceMaskRegion
from facefusion.uis.core import register_ui_component

FACE_MASK_TYPES_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
FACE_MASK_BLUR_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_BOX_GROUP : Optional[gradio.Group] = None
FACE_MASK_REGION_GROUP : Optional[gradio.Group] = None
FACE_MASK_PADDING_TOP_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_RIGHT_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_BOTTOM_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_PADDING_LEFT_SLIDER : Optional[gradio.Slider] = None
FACE_MASK_REGION_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global FACE_MASK_TYPES_CHECKBOX_GROUP
	global FACE_MASK_BLUR_SLIDER
	global FACE_MASK_BOX_GROUP
	global FACE_MASK_REGION_GROUP
	global FACE_MASK_PADDING_TOP_SLIDER
	global FACE_MASK_PADDING_RIGHT_SLIDER
	global FACE_MASK_PADDING_BOTTOM_SLIDER
	global FACE_MASK_PADDING_LEFT_SLIDER
	global FACE_MASK_REGION_CHECKBOX_GROUP

	has_box_mask = 'box' in facefusion.globals.face_mask_types
	has_region_mask = 'region' in facefusion.globals.face_mask_types
	FACE_MASK_TYPES_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('face_mask_types_checkbox_group_label'),
		choices = facefusion.choices.face_mask_types,
		value = facefusion.globals.face_mask_types
	)
	with gradio.Group(visible = has_box_mask) as FACE_MASK_BOX_GROUP:
		FACE_MASK_BLUR_SLIDER = gradio.Slider(
			label = wording.get('face_mask_blur_slider_label'),
			step = facefusion.choices.face_mask_blur_range[1] - facefusion.choices.face_mask_blur_range[0],
			minimum = facefusion.choices.face_mask_blur_range[0],
			maximum = facefusion.choices.face_mask_blur_range[-1],
			value = facefusion.globals.face_mask_blur
		)
		with gradio.Row():
			FACE_MASK_PADDING_TOP_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_top_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[0]
			)
			FACE_MASK_PADDING_RIGHT_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_right_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[1]
			)
		with gradio.Row():
			FACE_MASK_PADDING_BOTTOM_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_bottom_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[2]
			)
			FACE_MASK_PADDING_LEFT_SLIDER = gradio.Slider(
				label = wording.get('face_mask_padding_left_slider_label'),
				step = facefusion.choices.face_mask_padding_range[1] - facefusion.choices.face_mask_padding_range[0],
				minimum = facefusion.choices.face_mask_padding_range[0],
				maximum = facefusion.choices.face_mask_padding_range[-1],
				value = facefusion.globals.face_mask_padding[3]
			)
	with gradio.Row():
		FACE_MASK_REGION_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('face_mask_region_checkbox_group_label'),
			choices = facefusion.choices.face_mask_regions,
			value = facefusion.globals.face_mask_regions,
			visible = has_region_mask
		)
	register_ui_component('face_mask_types_checkbox_group', FACE_MASK_TYPES_CHECKBOX_GROUP)
	register_ui_component('face_mask_blur_slider', FACE_MASK_BLUR_SLIDER)
	register_ui_component('face_mask_padding_top_slider', FACE_MASK_PADDING_TOP_SLIDER)
	register_ui_component('face_mask_padding_right_slider', FACE_MASK_PADDING_RIGHT_SLIDER)
	register_ui_component('face_mask_padding_bottom_slider', FACE_MASK_PADDING_BOTTOM_SLIDER)
	register_ui_component('face_mask_padding_left_slider', FACE_MASK_PADDING_LEFT_SLIDER)
	register_ui_component('face_mask_region_checkbox_group', FACE_MASK_REGION_CHECKBOX_GROUP)


def listen() -> None:
	FACE_MASK_TYPES_CHECKBOX_GROUP.change(update_face_mask_type, inputs = FACE_MASK_TYPES_CHECKBOX_GROUP, outputs = [ FACE_MASK_TYPES_CHECKBOX_GROUP, FACE_MASK_BOX_GROUP, FACE_MASK_REGION_CHECKBOX_GROUP ])
	FACE_MASK_BLUR_SLIDER.change(update_face_mask_blur, inputs = FACE_MASK_BLUR_SLIDER)
	FACE_MASK_REGION_CHECKBOX_GROUP.change(update_face_mask_regions, inputs = FACE_MASK_REGION_CHECKBOX_GROUP, outputs = FACE_MASK_REGION_CHECKBOX_GROUP)
	face_mask_padding_sliders = [ FACE_MASK_PADDING_TOP_SLIDER, FACE_MASK_PADDING_RIGHT_SLIDER, FACE_MASK_PADDING_BOTTOM_SLIDER, FACE_MASK_PADDING_LEFT_SLIDER ]
	for face_mask_padding_slider in face_mask_padding_sliders:
		face_mask_padding_slider.change(update_face_mask_padding, inputs = face_mask_padding_sliders)


def update_face_mask_type(face_mask_types : List[FaceMaskType]) -> Tuple[gradio.CheckboxGroup, gradio.Group, gradio.CheckboxGroup]:
	if not face_mask_types:
		face_mask_types = facefusion.choices.face_mask_types
	facefusion.globals.face_mask_types = face_mask_types
	has_box_mask = 'box' in face_mask_types
	has_region_mask = 'region' in face_mask_types
	return gradio.CheckboxGroup(value = face_mask_types), gradio.Group(visible = has_box_mask), gradio.CheckboxGroup(visible = has_region_mask)


def update_face_mask_blur(face_mask_blur : float) -> None:
	facefusion.globals.face_mask_blur = face_mask_blur


def update_face_mask_padding(face_mask_padding_top : int, face_mask_padding_right : int, face_mask_padding_bottom : int, face_mask_padding_left : int) -> None:
	facefusion.globals.face_mask_padding = (face_mask_padding_top, face_mask_padding_right, face_mask_padding_bottom, face_mask_padding_left)


def update_face_mask_regions(face_mask_regions : List[FaceMaskRegion]) -> gradio.CheckboxGroup:
	if not face_mask_regions:
		face_mask_regions = facefusion.choices.face_mask_regions
	facefusion.globals.face_mask_regions = face_mask_regions
	return gradio.CheckboxGroup(value = face_mask_regions)
