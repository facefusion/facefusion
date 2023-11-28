from typing import List, Optional, Tuple, Any, Dict

import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.face_cache import clear_faces_cache
from facefusion.vision import get_video_frame, read_static_image, normalize_frame_color
from facefusion.face_analyser import get_many_faces
from facefusion.face_reference import clear_face_reference
from facefusion.typing import Frame, FaceSelectorMode
from facefusion.utilities import is_image, is_video
from facefusion.uis.core import get_ui_component, register_ui_component
from facefusion.uis.typing import ComponentName

FACE_SELECTOR_MODE_DROPDOWN : Optional[gradio.Dropdown] = None
REFERENCE_FACE_POSITION_GALLERY : Optional[gradio.Gallery] = None
REFERENCE_FACE_DISTANCE_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_SELECTOR_MODE_DROPDOWN
	global REFERENCE_FACE_POSITION_GALLERY
	global REFERENCE_FACE_DISTANCE_SLIDER

	reference_face_gallery_args: Dict[str, Any] =\
	{
		'label': wording.get('reference_face_gallery_label'),
		'object_fit': 'cover',
		'columns': 8,
		'allow_preview': False,
		'visible': 'reference' in facefusion.globals.face_selector_mode
	}
	if is_image(facefusion.globals.target_path):
		reference_frame = read_static_image(facefusion.globals.target_path)
		reference_face_gallery_args['value'] = extract_gallery_frames(reference_frame)
	if is_video(facefusion.globals.target_path):
		reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		reference_face_gallery_args['value'] = extract_gallery_frames(reference_frame)
	FACE_SELECTOR_MODE_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_selector_mode_dropdown_label'),
		choices = facefusion.choices.face_selector_modes,
		value = facefusion.globals.face_selector_mode
	)
	REFERENCE_FACE_POSITION_GALLERY = gradio.Gallery(**reference_face_gallery_args)
	REFERENCE_FACE_DISTANCE_SLIDER = gradio.Slider(
		label = wording.get('reference_face_distance_slider_label'),
		value = facefusion.globals.reference_face_distance,
		step = facefusion.choices.reference_face_distance_range[1] - facefusion.choices.reference_face_distance_range[0],
		minimum = facefusion.choices.reference_face_distance_range[0],
		maximum = facefusion.choices.reference_face_distance_range[-1],
		visible = 'reference' in facefusion.globals.face_selector_mode
	)
	register_ui_component('face_selector_mode_dropdown', FACE_SELECTOR_MODE_DROPDOWN)
	register_ui_component('reference_face_position_gallery', REFERENCE_FACE_POSITION_GALLERY)
	register_ui_component('reference_face_distance_slider', REFERENCE_FACE_DISTANCE_SLIDER)


def listen() -> None:
	FACE_SELECTOR_MODE_DROPDOWN.select(update_face_selector_mode, inputs = FACE_SELECTOR_MODE_DROPDOWN, outputs = [ REFERENCE_FACE_POSITION_GALLERY, REFERENCE_FACE_DISTANCE_SLIDER ])
	REFERENCE_FACE_POSITION_GALLERY.select(clear_and_update_reference_face_position)
	REFERENCE_FACE_DISTANCE_SLIDER.change(update_reference_face_distance, inputs = REFERENCE_FACE_DISTANCE_SLIDER)
	multi_component_names : List[ComponentName] =\
	[
		'target_image',
		'target_video'
	]
	for component_name in multi_component_names:
		component = get_ui_component(component_name)
		if component:
			for method in [ 'upload', 'change', 'clear' ]:
				getattr(component, method)(update_reference_face_position)
				getattr(component, method)(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)
	change_one_component_names : List[ComponentName] =\
	[
		'face_analyser_order_dropdown',
		'face_analyser_age_dropdown',
		'face_analyser_gender_dropdown'
	]
	for component_name in change_one_component_names:
		component = get_ui_component(component_name)
		if component:
			component.change(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)
	change_two_component_names : List[ComponentName] =\
	[
		'face_detector_model_dropdown',
		'face_detector_size_dropdown',
		'face_detector_score_slider'
	]
	for component_name in change_two_component_names:
		component = get_ui_component(component_name)
		if component:
			component.change(clear_and_update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)
	preview_frame_slider = get_ui_component('preview_frame_slider')
	if preview_frame_slider:
		preview_frame_slider.change(update_reference_frame_number, inputs = preview_frame_slider)
		preview_frame_slider.release(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)


def update_face_selector_mode(face_selector_mode : FaceSelectorMode) -> Tuple[gradio.Gallery, gradio.Slider]:
	if face_selector_mode == 'reference':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = True), gradio.Slider(visible = True)
	if face_selector_mode == 'one':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)
	if face_selector_mode == 'many':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)


def clear_and_update_reference_face_position(event : gradio.SelectData) -> gradio.Gallery:
	clear_face_reference()
	clear_faces_cache()
	update_reference_face_position(event.index)
	return update_reference_position_gallery()


def update_reference_face_position(reference_face_position : int = 0) -> None:
	facefusion.globals.reference_face_position = reference_face_position


def update_reference_face_distance(reference_face_distance : float) -> None:
	facefusion.globals.reference_face_distance = reference_face_distance


def update_reference_frame_number(reference_frame_number : int) -> None:
	facefusion.globals.reference_frame_number = reference_frame_number


def clear_and_update_reference_position_gallery() -> gradio.Gallery:
	clear_face_reference()
	clear_faces_cache()
	return update_reference_position_gallery()


def update_reference_position_gallery() -> gradio.Gallery:
	gallery_frames = []
	if is_image(facefusion.globals.target_path):
		reference_frame = read_static_image(facefusion.globals.target_path)
		gallery_frames = extract_gallery_frames(reference_frame)
	if is_video(facefusion.globals.target_path):
		reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		gallery_frames = extract_gallery_frames(reference_frame)
	if gallery_frames:
		return gradio.Gallery(value = gallery_frames)
	return gradio.Gallery(value = None)


def extract_gallery_frames(reference_frame : Frame) -> List[Frame]:
	crop_frames = []
	faces = get_many_faces(reference_frame)
	for face in faces:
		start_x, start_y, end_x, end_y = map(int, face.bbox)
		padding_x = int((end_x - start_x) * 0.25)
		padding_y = int((end_y - start_y) * 0.25)
		start_x = max(0, start_x - padding_x)
		start_y = max(0, start_y - padding_y)
		end_x = max(0, end_x + padding_x)
		end_y = max(0, end_y + padding_y)
		crop_frame = reference_frame[start_y:end_y, start_x:end_x]
		crop_frame = normalize_frame_color(crop_frame)
		crop_frames.append(crop_frame)
	return crop_frames
