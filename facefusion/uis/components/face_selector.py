from typing import List, Optional, Tuple

import gradio
from gradio_rangeslider import RangeSlider

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import calc_float_step, calc_int_step
from facefusion.face_analyser import get_many_faces
from facefusion.face_selector import sort_and_filter_faces
from facefusion.face_store import clear_reference_faces, clear_static_faces
from facefusion.filesystem import is_image, is_video
from facefusion.types import FaceSelectorMode, FaceSelectorOrder, Gender, Race, VisionFrame
from facefusion.uis.core import get_ui_component, get_ui_components, register_ui_component
from facefusion.uis.types import ComponentOptions
from facefusion.uis.ui_helper import convert_str_none
from facefusion.vision import normalize_frame_color, read_static_image, read_video_frame

FACE_SELECTOR_MODE_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SELECTOR_ORDER_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SELECTOR_GENDER_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SELECTOR_RACE_DROPDOWN : Optional[gradio.Dropdown] = None
FACE_SELECTOR_AGE_RANGE_SLIDER : Optional[RangeSlider] = None
REFERENCE_FACE_POSITION_GALLERY : Optional[gradio.Gallery] = None
REFERENCE_FACE_DISTANCE_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_SELECTOR_MODE_DROPDOWN
	global FACE_SELECTOR_ORDER_DROPDOWN
	global FACE_SELECTOR_GENDER_DROPDOWN
	global FACE_SELECTOR_RACE_DROPDOWN
	global FACE_SELECTOR_AGE_RANGE_SLIDER
	global REFERENCE_FACE_POSITION_GALLERY
	global REFERENCE_FACE_DISTANCE_SLIDER

	reference_face_gallery_options : ComponentOptions =\
	{
		'label': wording.get('uis.reference_face_gallery'),
		'object_fit': 'cover',
		'columns': 7,
		'allow_preview': False,
		'elem_classes': 'box-face-selector',
		'visible': 'reference' in state_manager.get_item('face_selector_mode')
	}
	if is_image(state_manager.get_item('target_path')):
		reference_frame = read_static_image(state_manager.get_item('target_path'))
		reference_face_gallery_options['value'] = extract_gallery_frames(reference_frame)
	if is_video(state_manager.get_item('target_path')):
		reference_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		reference_face_gallery_options['value'] = extract_gallery_frames(reference_frame)
	FACE_SELECTOR_MODE_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.face_selector_mode_dropdown'),
		choices = facefusion.choices.face_selector_modes,
		value = state_manager.get_item('face_selector_mode')
	)
	REFERENCE_FACE_POSITION_GALLERY = gradio.Gallery(**reference_face_gallery_options)
	with gradio.Group():
		with gradio.Row():
			FACE_SELECTOR_ORDER_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.face_selector_order_dropdown'),
				choices = facefusion.choices.face_selector_orders,
				value = state_manager.get_item('face_selector_order')
			)
			FACE_SELECTOR_GENDER_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.face_selector_gender_dropdown'),
				choices = [ 'none' ] + facefusion.choices.face_selector_genders,
				value = state_manager.get_item('face_selector_gender') or 'none'
			)
			FACE_SELECTOR_RACE_DROPDOWN = gradio.Dropdown(
				label = wording.get('uis.face_selector_race_dropdown'),
				choices = ['none'] + facefusion.choices.face_selector_races,
				value = state_manager.get_item('face_selector_race') or 'none'
			)
		with gradio.Row():
			face_selector_age_start = state_manager.get_item('face_selector_age_start') or facefusion.choices.face_selector_age_range[0]
			face_selector_age_end = state_manager.get_item('face_selector_age_end') or facefusion.choices.face_selector_age_range[-1]
			FACE_SELECTOR_AGE_RANGE_SLIDER = RangeSlider(
				label = wording.get('uis.face_selector_age_range_slider'),
				minimum = facefusion.choices.face_selector_age_range[0],
				maximum = facefusion.choices.face_selector_age_range[-1],
				value = (face_selector_age_start, face_selector_age_end),
				step = calc_int_step(facefusion.choices.face_selector_age_range)
			)
	REFERENCE_FACE_DISTANCE_SLIDER = gradio.Slider(
		label = wording.get('uis.reference_face_distance_slider'),
		value = state_manager.get_item('reference_face_distance'),
		step = calc_float_step(facefusion.choices.reference_face_distance_range),
		minimum = facefusion.choices.reference_face_distance_range[0],
		maximum = facefusion.choices.reference_face_distance_range[-1],
		visible = 'reference' in state_manager.get_item('face_selector_mode')
	)
	register_ui_component('face_selector_mode_dropdown', FACE_SELECTOR_MODE_DROPDOWN)
	register_ui_component('face_selector_order_dropdown', FACE_SELECTOR_ORDER_DROPDOWN)
	register_ui_component('face_selector_gender_dropdown', FACE_SELECTOR_GENDER_DROPDOWN)
	register_ui_component('face_selector_race_dropdown', FACE_SELECTOR_RACE_DROPDOWN)
	register_ui_component('face_selector_age_range_slider', FACE_SELECTOR_AGE_RANGE_SLIDER)
	register_ui_component('reference_face_position_gallery', REFERENCE_FACE_POSITION_GALLERY)
	register_ui_component('reference_face_distance_slider', REFERENCE_FACE_DISTANCE_SLIDER)


def listen() -> None:
	FACE_SELECTOR_MODE_DROPDOWN.change(update_face_selector_mode, inputs = FACE_SELECTOR_MODE_DROPDOWN, outputs = [ REFERENCE_FACE_POSITION_GALLERY, REFERENCE_FACE_DISTANCE_SLIDER ])
	FACE_SELECTOR_ORDER_DROPDOWN.change(update_face_selector_order, inputs = FACE_SELECTOR_ORDER_DROPDOWN, outputs = REFERENCE_FACE_POSITION_GALLERY)
	FACE_SELECTOR_GENDER_DROPDOWN.change(update_face_selector_gender, inputs = FACE_SELECTOR_GENDER_DROPDOWN, outputs = REFERENCE_FACE_POSITION_GALLERY)
	FACE_SELECTOR_RACE_DROPDOWN.change(update_face_selector_race, inputs = FACE_SELECTOR_RACE_DROPDOWN, outputs = REFERENCE_FACE_POSITION_GALLERY)
	FACE_SELECTOR_AGE_RANGE_SLIDER.release(update_face_selector_age_range, inputs = FACE_SELECTOR_AGE_RANGE_SLIDER, outputs = REFERENCE_FACE_POSITION_GALLERY)
	REFERENCE_FACE_POSITION_GALLERY.select(clear_and_update_reference_face_position)
	REFERENCE_FACE_DISTANCE_SLIDER.release(update_reference_face_distance, inputs = REFERENCE_FACE_DISTANCE_SLIDER)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(update_reference_face_position)
			getattr(ui_component, method)(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	for ui_component in get_ui_components(
	[
		'face_detector_model_dropdown',
		'face_detector_size_dropdown',
		'face_detector_angles_checkbox_group'
	]):
		ui_component.change(clear_and_update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	face_detector_score_slider = get_ui_component('face_detector_score_slider')
	if face_detector_score_slider:
		face_detector_score_slider.release(clear_and_update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	preview_frame_slider = get_ui_component('preview_frame_slider')
	if preview_frame_slider:
		for method in [ 'change', 'release' ]:
			getattr(preview_frame_slider, method)(update_reference_frame_number, inputs = preview_frame_slider, show_progress = 'hidden')
			getattr(preview_frame_slider, method)(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY, show_progress = 'hidden')


def update_face_selector_mode(face_selector_mode : FaceSelectorMode) -> Tuple[gradio.Gallery, gradio.Slider]:
	state_manager.set_item('face_selector_mode', face_selector_mode)
	if face_selector_mode == 'many':
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)
	if face_selector_mode == 'one':
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)
	if face_selector_mode == 'reference':
		return gradio.Gallery(visible = True), gradio.Slider(visible = True)


def update_face_selector_order(face_analyser_order : FaceSelectorOrder) -> gradio.Gallery:
	state_manager.set_item('face_selector_order', convert_str_none(face_analyser_order))
	return update_reference_position_gallery()


def update_face_selector_gender(face_selector_gender : Gender) -> gradio.Gallery:
	state_manager.set_item('face_selector_gender', convert_str_none(face_selector_gender))
	return update_reference_position_gallery()


def update_face_selector_race(face_selector_race : Race) -> gradio.Gallery:
	state_manager.set_item('face_selector_race', convert_str_none(face_selector_race))
	return update_reference_position_gallery()


def update_face_selector_age_range(face_selector_age_range : Tuple[float, float]) -> gradio.Gallery:
	face_selector_age_start, face_selector_age_end = face_selector_age_range
	state_manager.set_item('face_selector_age_start', int(face_selector_age_start))
	state_manager.set_item('face_selector_age_end', int(face_selector_age_end))
	return update_reference_position_gallery()


def clear_and_update_reference_face_position(event : gradio.SelectData) -> gradio.Gallery:
	clear_reference_faces()
	clear_static_faces()
	update_reference_face_position(event.index)
	return update_reference_position_gallery()


def update_reference_face_position(reference_face_position : int = 0) -> None:
	state_manager.set_item('reference_face_position', reference_face_position)


def update_reference_face_distance(reference_face_distance : float) -> None:
	state_manager.set_item('reference_face_distance', reference_face_distance)


def update_reference_frame_number(reference_frame_number : int) -> None:
	state_manager.set_item('reference_frame_number', reference_frame_number)


def clear_and_update_reference_position_gallery() -> gradio.Gallery:
	clear_reference_faces()
	clear_static_faces()
	return update_reference_position_gallery()


def update_reference_position_gallery() -> gradio.Gallery:
	gallery_vision_frames = []
	if is_image(state_manager.get_item('target_path')):
		temp_vision_frame = read_static_image(state_manager.get_item('target_path'))
		gallery_vision_frames = extract_gallery_frames(temp_vision_frame)
	if is_video(state_manager.get_item('target_path')):
		temp_vision_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		gallery_vision_frames = extract_gallery_frames(temp_vision_frame)
	if gallery_vision_frames:
		return gradio.Gallery(value = gallery_vision_frames)
	return gradio.Gallery(value = None)


def extract_gallery_frames(temp_vision_frame : VisionFrame) -> List[VisionFrame]:
	gallery_vision_frames = []
	faces = sort_and_filter_faces(get_many_faces([ temp_vision_frame ]))

	for face in faces:
		start_x, start_y, end_x, end_y = map(int, face.bounding_box)
		padding_x = int((end_x - start_x) * 0.25)
		padding_y = int((end_y - start_y) * 0.25)
		start_x = max(0, start_x - padding_x)
		start_y = max(0, start_y - padding_y)
		end_x = max(0, end_x + padding_x)
		end_y = max(0, end_y + padding_y)
		crop_vision_frame = temp_vision_frame[start_y:end_y, start_x:end_x]
		crop_vision_frame = normalize_frame_color(crop_vision_frame)
		gallery_vision_frames.append(crop_vision_frame)
	return gallery_vision_frames
