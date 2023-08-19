from time import sleep
from typing import Any, Dict, Tuple, List, Optional
import cv2
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.capturer import get_video_frame, get_video_frame_total
from facefusion.face_analyser import get_one_face
from facefusion.face_reference import get_face_reference, set_face_reference
from facefusion.predictor import predict_frame
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.typing import Frame
from facefusion.uis import core as ui
from facefusion.uis.typing import ComponentName, Update
from facefusion.utilities import is_video, is_image

PREVIEW_IMAGE : Optional[gradio.Image] = None
PREVIEW_FRAME_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global PREVIEW_IMAGE
	global PREVIEW_FRAME_SLIDER

	with gradio.Box():
		preview_image_args: Dict[str, Any] = {
			'label': wording.get('preview_image_label')
		}
		preview_frame_slider_args: Dict[str, Any] = {
			'label': wording.get('preview_frame_slider_label'),
			'step': 1,
			'visible': False
		}
		if is_image(facefusion.globals.target_path):
			target_frame = cv2.imread(facefusion.globals.target_path)
			preview_frame = extract_preview_frame(target_frame)
			preview_image_args['value'] = ui.normalize_frame(preview_frame)
		if is_video(facefusion.globals.target_path):
			temp_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
			preview_frame = extract_preview_frame(temp_frame)
			preview_image_args['value'] = ui.normalize_frame(preview_frame)
			preview_image_args['visible'] = True
			preview_frame_slider_args['value'] = facefusion.globals.reference_frame_number
			preview_frame_slider_args['maximum'] = get_video_frame_total(facefusion.globals.target_path)
			preview_frame_slider_args['visible'] = True
		PREVIEW_IMAGE = gradio.Image(**preview_image_args)
		PREVIEW_FRAME_SLIDER = gradio.Slider(**preview_frame_slider_args)
		ui.register_component('preview_frame_slider', PREVIEW_FRAME_SLIDER)


def listen() -> None:
	PREVIEW_FRAME_SLIDER.change(update, inputs = PREVIEW_FRAME_SLIDER, outputs = [ PREVIEW_IMAGE, PREVIEW_FRAME_SLIDER ])
	update_component_names : List[ComponentName] =\
	[
		'source_file',
		'target_file',
		'face_recognition_dropdown',
		'reference_face_distance_slider',
		'frame_processors_checkbox_group'
	]
	for component_name in update_component_names:
		component = ui.get_component(component_name)
		if component:
			component.change(update, inputs = PREVIEW_FRAME_SLIDER, outputs = [ PREVIEW_IMAGE, PREVIEW_FRAME_SLIDER ])
	select_component_names : List[ComponentName] =\
	[
		'reference_face_position_gallery',
		'face_analyser_direction_dropdown',
		'face_analyser_age_dropdown',
		'face_analyser_gender_dropdown'
	]
	for component_name in select_component_names:
		component = ui.get_component(component_name)
		if component:
			component.select(update, inputs = PREVIEW_FRAME_SLIDER, outputs = [ PREVIEW_IMAGE, PREVIEW_FRAME_SLIDER ])


def update(frame_number : int = 0) -> Tuple[Update, Update]:
	sleep(0.1)
	if is_image(facefusion.globals.target_path):
		target_frame = cv2.imread(facefusion.globals.target_path)
		preview_frame = extract_preview_frame(target_frame)
		return gradio.update(value = ui.normalize_frame(preview_frame)), gradio.update(value = None, maximum = None, visible = False)
	if is_video(facefusion.globals.target_path):
		facefusion.globals.reference_frame_number = frame_number
		video_frame_total = get_video_frame_total(facefusion.globals.target_path)
		temp_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		preview_frame = extract_preview_frame(temp_frame)
		return gradio.update(value = ui.normalize_frame(preview_frame)), gradio.update(maximum = video_frame_total, visible = True)
	return gradio.update(value = None), gradio.update(value = None, maximum = None, visible = False)


def extract_preview_frame(temp_frame : Frame) -> Frame:
	if predict_frame(temp_frame):
		return cv2.GaussianBlur(temp_frame, (99, 99), 0)
	source_face = get_one_face(cv2.imread(facefusion.globals.source_path)) if facefusion.globals.source_path else None
	temp_frame = reduce_preview_frame(temp_frame)
	if 'reference' in facefusion.globals.face_recognition and not get_face_reference():
		reference_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		reference_face = get_one_face(reference_frame, facefusion.globals.reference_face_position)
		set_face_reference(reference_face)
	reference_face = get_face_reference() if 'reference' in facefusion.globals.face_recognition else None
	for frame_processor in facefusion.globals.frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		if frame_processor_module.pre_process():
			temp_frame = frame_processor_module.process_frame(
				source_face,
				reference_face,
				temp_frame
			)
	return temp_frame


def reduce_preview_frame(temp_frame : Frame, max_height : int = 480) -> Frame:
	height, width = temp_frame.shape[:2]
	if height > max_height:
		scale = max_height / height
		max_width = int(width * scale)
		temp_frame = cv2.resize(temp_frame, (max_width, max_height))
	return temp_frame
