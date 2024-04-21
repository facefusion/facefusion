from typing import Any, Dict, Optional
from time import sleep
import cv2
import gradio
import numpy

import facefusion.globals
from facefusion import logger, wording
from facefusion.audio import get_audio_frame, create_empty_audio_frame
from facefusion.common_helper import get_first
from facefusion.core import conditional_append_reference_faces
from facefusion.face_analyser import get_average_face, clear_face_analyser
from facefusion.face_store import clear_static_faces, get_reference_faces, clear_reference_faces
from facefusion.typing import Face, FaceSet, AudioFrame, VisionFrame
from facefusion.vision import get_video_frame, count_video_frame_total, normalize_frame_color, resize_frame_resolution, read_static_image, read_static_images
from facefusion.filesystem import is_image, is_video, filter_audio_paths
from facefusion.content_analyser import analyse_frame
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.uis.core import get_ui_component, get_ui_components, register_ui_component
from facefusion.uis.typing import Update

PREVIEW_IMAGE : Optional[gradio.Image] = None
PREVIEW_FRAME_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global PREVIEW_IMAGE
	global PREVIEW_FRAME_SLIDER

	preview_image_args : Dict[str, Any] =\
	{
		'label': wording.get('uis.preview_image'),
		'interactive': False
	}
	preview_frame_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('uis.preview_frame_slider'),
		'step': 1,
		'minimum': 0,
		'maximum': 100,
		'visible': False
	}
	conditional_append_reference_faces()
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_frames = read_static_images(facefusion.globals.source_paths)
	source_face = get_average_face(source_frames)
	source_audio_path = get_first(filter_audio_paths(facefusion.globals.source_paths))
	source_audio_frame = create_empty_audio_frame()
	if source_audio_path and facefusion.globals.output_video_fps and facefusion.globals.reference_frame_number:
		temp_audio_frame = get_audio_frame(source_audio_path, facefusion.globals.output_video_fps, facefusion.globals.reference_frame_number)
		if numpy.any(temp_audio_frame):
			source_audio_frame = temp_audio_frame
	if is_image(facefusion.globals.target_path):
		target_vision_frame = read_static_image(facefusion.globals.target_path)
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, target_vision_frame)
		preview_image_args['value'] = normalize_frame_color(preview_vision_frame)
	if is_video(facefusion.globals.target_path):
		temp_vision_frame = get_video_frame(facefusion.globals.target_path, facefusion.globals.reference_frame_number)
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, temp_vision_frame)
		preview_image_args['value'] = normalize_frame_color(preview_vision_frame)
		preview_image_args['visible'] = True
		preview_frame_slider_args['value'] = facefusion.globals.reference_frame_number
		preview_frame_slider_args['maximum'] = count_video_frame_total(facefusion.globals.target_path)
		preview_frame_slider_args['visible'] = True
	PREVIEW_IMAGE = gradio.Image(**preview_image_args)
	PREVIEW_FRAME_SLIDER = gradio.Slider(**preview_frame_slider_args)
	register_ui_component('preview_frame_slider', PREVIEW_FRAME_SLIDER)


def listen() -> None:
	PREVIEW_FRAME_SLIDER.release(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)
	reference_face_position_gallery = get_ui_component('reference_face_position_gallery')
	if reference_face_position_gallery:
		reference_face_position_gallery.select(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'source_audio',
		'source_image',
		'target_image',
		'target_video'
	]):
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_frame_slider, outputs = PREVIEW_FRAME_SLIDER)

	for ui_component in get_ui_components(
	[
		'face_debugger_items_checkbox_group',
		'frame_colorizer_size_dropdown',
		'face_selector_mode_dropdown',
		'face_mask_types_checkbox_group',
		'face_mask_region_checkbox_group',
		'face_analyser_order_dropdown',
		'face_analyser_age_dropdown',
		'face_analyser_gender_dropdown'
	]):
		ui_component.change(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'face_enhancer_blend_slider',
		'frame_colorizer_blend_slider',
		'frame_enhancer_blend_slider',
		'trim_frame_start_slider',
		'trim_frame_end_slider',
		'reference_face_distance_slider',
		'face_mask_blur_slider',
		'face_mask_padding_top_slider',
		'face_mask_padding_bottom_slider',
		'face_mask_padding_left_slider',
		'face_mask_padding_right_slider',
		'output_video_fps_slider'
	]):
		ui_component.release(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'frame_processors_checkbox_group',
		'face_enhancer_model_dropdown',
		'face_swapper_model_dropdown',
		'frame_colorizer_model_dropdown',
		'frame_enhancer_model_dropdown',
		'lip_syncer_model_dropdown',
		'face_detector_model_dropdown',
		'face_detector_size_dropdown'
	]):
		ui_component.change(clear_and_update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'face_detector_score_slider',
		'face_landmarker_score_slider'
	]):
		ui_component.release(clear_and_update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)


def clear_and_update_preview_image(frame_number : int = 0) -> Update:
	clear_face_analyser()
	clear_reference_faces()
	clear_static_faces()
	return update_preview_image(frame_number)


def update_preview_image(frame_number : int = 0) -> Update:
	for frame_processor in facefusion.globals.frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		while not frame_processor_module.post_check():
			logger.disable()
			sleep(0.5)
		logger.enable()
	conditional_append_reference_faces()
	reference_faces = get_reference_faces() if 'reference' in facefusion.globals.face_selector_mode else None
	source_frames = read_static_images(facefusion.globals.source_paths)
	source_face = get_average_face(source_frames)
	source_audio_path = get_first(filter_audio_paths(facefusion.globals.source_paths))
	source_audio_frame = create_empty_audio_frame()
	if source_audio_path and facefusion.globals.output_video_fps and facefusion.globals.reference_frame_number:
		reference_audio_frame_number = facefusion.globals.reference_frame_number
		if facefusion.globals.trim_frame_start:
			reference_audio_frame_number -= facefusion.globals.trim_frame_start
		temp_audio_frame = get_audio_frame(source_audio_path, facefusion.globals.output_video_fps, reference_audio_frame_number)
		if numpy.any(temp_audio_frame):
			source_audio_frame = temp_audio_frame
	if is_image(facefusion.globals.target_path):
		target_vision_frame = read_static_image(facefusion.globals.target_path)
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, target_vision_frame)
		preview_vision_frame = normalize_frame_color(preview_vision_frame)
		return gradio.update(value = preview_vision_frame)
	if is_video(facefusion.globals.target_path):
		temp_vision_frame = get_video_frame(facefusion.globals.target_path, frame_number)
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, temp_vision_frame)
		preview_vision_frame = normalize_frame_color(preview_vision_frame)
		return gradio.update(value = preview_vision_frame)
	return gradio.update(value = None)


def update_preview_frame_slider() -> Update:
	if is_video(facefusion.globals.target_path):
		video_frame_total = count_video_frame_total(facefusion.globals.target_path)
		return gradio.update(maximum = video_frame_total, visible = True)
	return gradio.update(value = None, maximum = None, visible = False)


def process_preview_frame(reference_faces : FaceSet, source_face : Face, source_audio_frame : AudioFrame, target_vision_frame : VisionFrame) -> VisionFrame:
	target_vision_frame = resize_frame_resolution(target_vision_frame, (640, 640))
	if analyse_frame(target_vision_frame):
		return cv2.GaussianBlur(target_vision_frame, (99, 99), 0)
	for frame_processor in facefusion.globals.frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		logger.disable()
		if frame_processor_module.pre_process('preview'):
			logger.enable()
			target_vision_frame = frame_processor_module.process_frame(
			{
				'reference_faces': reference_faces,
				'source_face': source_face,
				'source_audio_frame': source_audio_frame,
				'target_vision_frame': target_vision_frame
			})
	return target_vision_frame
