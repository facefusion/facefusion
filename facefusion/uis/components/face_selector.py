from typing import List, Optional, Tuple, Any, Dict

import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.face_store import clear_static_faces, clear_reference_faces
from facefusion.vision import get_video_frame, read_static_image, normalize_frame_color
from facefusion.filesystem import is_image, is_video
from facefusion.face_analyser import get_many_faces
from facefusion.typing import VisionFrame, FaceSelectorMode
from facefusion.uis.core import get_ui_component, get_ui_components, register_ui_component

FACE_SELECTOR_MODE_DROPDOWN : Optional[gradio.Dropdown] = None
REFERENCE_FACE_POSITION_GALLERY : Optional[gradio.Gallery] = None
REFERENCE_FACE_DISTANCE_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_SELECTOR_MODE_DROPDOWN
	global REFERENCE_FACE_POSITION_GALLERY
	global REFERENCE_FACE_DISTANCE_SLIDER

	reference_face_gallery_args : Dict[str, Any] =\
	{
		'label': wording.get('uis.reference_face_gallery'),
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
		label = wording.get('uis.face_selector_mode_dropdown'),
		choices = facefusion.choices.face_selector_modes,
		value = facefusion.globals.face_selector_mode
	)
	REFERENCE_FACE_POSITION_GALLERY = gradio.Gallery(**reference_face_gallery_args)
	REFERENCE_FACE_DISTANCE_SLIDER = gradio.Slider(
		label = wording.get('uis.reference_face_distance_slider'),
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
	FACE_SELECTOR_MODE_DROPDOWN.change(update_face_selector_mode, inputs = FACE_SELECTOR_MODE_DROPDOWN, outputs = [ REFERENCE_FACE_POSITION_GALLERY, REFERENCE_FACE_DISTANCE_SLIDER ])
	REFERENCE_FACE_POSITION_GALLERY.select(clear_and_update_reference_face_position)
	REFERENCE_FACE_DISTANCE_SLIDER.release(update_reference_face_distance, inputs = REFERENCE_FACE_DISTANCE_SLIDER)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(ui_component, method)(update_reference_face_position)
			getattr(ui_component, method)(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	for ui_component in get_ui_components(
	[
		'face_analyser_order_dropdown',
		'face_analyser_age_dropdown',
		'face_analyser_gender_dropdown'
	]):
		ui_component.change(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	for ui_component in get_ui_components(
	[
		'face_detector_model_dropdown',
		'face_detector_size_dropdown'
	]):
		ui_component.change(clear_and_update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)

	for ui_component in get_ui_components(
	[
		'face_detector_score_slider',
		'face_landmarker_score_slider'
	]):
		ui_component.release(clear_and_update_reference_position_gallery, outputs=REFERENCE_FACE_POSITION_GALLERY)

	preview_frame_slider = get_ui_component('preview_frame_slider')
	if preview_frame_slider:
		preview_frame_slider.change(update_reference_frame_number, inputs = preview_frame_slider)
		preview_frame_slider.release(update_reference_position_gallery, outputs = REFERENCE_FACE_POSITION_GALLERY)


def update_face_selector_mode(face_selector_mode : FaceSelectorMode) -> Tuple[gradio.Gallery, gradio.Slider]:
	if face_selector_mode == 'many':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)
	if face_selector_mode == 'one':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = False), gradio.Slider(visible = False)
	if face_selector_mode == 'reference':
		facefusion.globals.face_selector_mode = face_selector_mode
		return gradio.Gallery(visible = True), gradio.Slider(visible = True)


def clear_and_update_reference_face_position(event : gradio.SelectData) -> gradio.Gallery:
	clear_reference_faces()
	clear_static_faces()
	update_reference_face_position(event.index)
	return update_reference_position_gallery()


def update_reference_face_position(reference_face_position : int = 0) -> None:
	facefusion.globals.reference_face_position = reference_face_position


def update_reference_face_distance(reference_face_distance : float) -> None:
	facefusion.globals.reference_face_distance = reference_face_distance


def update_reference_frame_number(reference_frame_number : int) -> None:
	facefusion.globals.reference_frame_number = reference_frame_number


def clear_and_update_reference_position_gallery() -> gradio.Gallery:
	clear_reference_faces()
	clear_static_faces()
	return update_reference_position_gallery()


def update_reference_position_gallery() -> gradio.Gallery:
	gallery_vision_frames = []
	if is_image(facefusion.globals.target_path):
		temp_vision_frame = read_static_image(facefusion.globals.target_path)
		gallery_vision_frames = extract_gallery_frames(temp_vision_frame)
	if is_video(facefusion.globals.target_path):
		temp_vision_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		gallery_vision_frames = extract_gallery_frames(temp_vision_frame)
	if gallery_vision_frames:
		return gradio.Gallery(value = gallery_vision_frames)
	return gradio.Gallery(value = None)


def extract_gallery_frames(temp_vision_frame : VisionFrame) -> List[VisionFrame]:
	gallery_vision_frames = []
	faces = get_many_faces(temp_vision_frame)

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
