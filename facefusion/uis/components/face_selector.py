from typing import List, Optional, Tuple, Any, Dict

import gradio

import facefusion.choices
import facefusion.globals
from facefusion import wording
from facefusion.vision import get_video_frame, normalize_frame_color, read_static_image
from facefusion.face_analyser import get_many_faces
from facefusion.face_reference import clear_face_reference
from facefusion.typing import Frame, FaceRecognition
from facefusion.uis import core as ui
from facefusion.uis.typing import ComponentName, Update
from facefusion.utilities import is_image, is_video

FACE_RECOGNITION_DROPDOWN : Optional[gradio.Dropdown] = None
REFERENCE_FACE_POSITION_GALLERY : Optional[gradio.Gallery] = None
REFERENCE_FACE_DISTANCE_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global FACE_RECOGNITION_DROPDOWN
	global REFERENCE_FACE_POSITION_GALLERY
	global REFERENCE_FACE_DISTANCE_SLIDER

	reference_face_gallery_args: Dict[str, Any] =\
	{
		'label': wording.get('reference_face_gallery_label'),
		'height': 120,
		'object_fit': 'cover',
		'columns': 10,
		'allow_preview': False,
		'visible': 'reference' in facefusion.globals.face_recognition
	}
	if is_image(facefusion.globals.target_path):
		reference_frame = read_static_image(facefusion.globals.target_path)
		reference_face_gallery_args['value'] = extract_gallery_frames(reference_frame)
	if is_video(facefusion.globals.target_path):
		reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		reference_face_gallery_args['value'] = extract_gallery_frames(reference_frame)
	FACE_RECOGNITION_DROPDOWN = gradio.Dropdown(
		label = wording.get('face_recognition_dropdown_label'),
		choices = facefusion.choices.face_recognition,
		value = facefusion.globals.face_recognition
	)
	REFERENCE_FACE_POSITION_GALLERY = gradio.Gallery(**reference_face_gallery_args)
	REFERENCE_FACE_DISTANCE_SLIDER = gradio.Slider(
		label = wording.get('reference_face_distance_slider_label'),
		value = facefusion.globals.reference_face_distance,
		maximum = 3,
		step = 0.05,
		visible = 'reference' in facefusion.globals.face_recognition
	)
	ui.register_component('face_recognition_dropdown', FACE_RECOGNITION_DROPDOWN)
	ui.register_component('reference_face_position_gallery', REFERENCE_FACE_POSITION_GALLERY)
	ui.register_component('reference_face_distance_slider', REFERENCE_FACE_DISTANCE_SLIDER)


def listen() -> None:
	FACE_RECOGNITION_DROPDOWN.select(update_face_recognition, inputs = FACE_RECOGNITION_DROPDOWN, outputs = [ REFERENCE_FACE_POSITION_GALLERY, REFERENCE_FACE_DISTANCE_SLIDER ])
	REFERENCE_FACE_POSITION_GALLERY.select(clear_and_update_face_reference_position)
	REFERENCE_FACE_DISTANCE_SLIDER.change(update_reference_face_distance, inputs = REFERENCE_FACE_DISTANCE_SLIDER)
	multi_component_names : List[ComponentName] =\
	[
		'source_image',
		'target_image',
		'target_video'
	]
	for component_name in multi_component_names:
		component = ui.get_component(component_name)
		if component:
			for method in [ 'upload', 'change', 'clear' ]:
				getattr(component, method)(update_face_reference_position, outputs = REFERENCE_FACE_POSITION_GALLERY)
	select_component_names : List[ComponentName] =\
	[
		'face_analyser_direction_dropdown',
		'face_analyser_age_dropdown',
		'face_analyser_gender_dropdown'
	]
	for component_name in select_component_names:
		component = ui.get_component(component_name)
		if component:
			component.select(update_face_reference_position, outputs = REFERENCE_FACE_POSITION_GALLERY)
	preview_frame_slider = ui.get_component('preview_frame_slider')
	if preview_frame_slider:
		preview_frame_slider.release(update_face_reference_position, outputs = REFERENCE_FACE_POSITION_GALLERY)


def update_face_recognition(face_recognition : FaceRecognition) -> Tuple[Update, Update]:
	if face_recognition == 'reference':
		facefusion.globals.face_recognition = face_recognition
		return gradio.update(visible = True), gradio.update(visible = True)
	if face_recognition == 'many':
		facefusion.globals.face_recognition = face_recognition
		return gradio.update(visible = False), gradio.update(visible = False)


def clear_and_update_face_reference_position(event: gradio.SelectData) -> Update:
	clear_face_reference()
	return update_face_reference_position(event.index)


def update_face_reference_position(reference_face_position : int = 0) -> Update:
	gallery_frames = []
	facefusion.globals.reference_face_position = reference_face_position
	if is_image(facefusion.globals.target_path):
		reference_frame = read_static_image(facefusion.globals.target_path)
		gallery_frames = extract_gallery_frames(reference_frame)
	if is_video(facefusion.globals.target_path):
		reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		gallery_frames = extract_gallery_frames(reference_frame)
	if gallery_frames:
		return gradio.update(value = gallery_frames)
	return gradio.update(value = None)


def update_reference_face_distance(reference_face_distance : float) -> Update:
	facefusion.globals.reference_face_distance = reference_face_distance
	return gradio.update(value = reference_face_distance)


def extract_gallery_frames(reference_frame : Frame) -> List[Frame]:
	crop_frames = []
	faces = get_many_faces(reference_frame)
	for face in faces:
		start_x, start_y, end_x, end_y = map(int, face['bbox'])
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
