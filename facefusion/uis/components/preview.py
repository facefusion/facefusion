from time import sleep
from typing import Optional

import cv2
import gradio
import numpy

from facefusion import logger, process_manager, state_manager, wording
from facefusion.audio import create_empty_audio_frame, get_audio_frame
from facefusion.common_helper import get_first
from facefusion.content_analyser import analyse_frame
from facefusion.core import conditional_append_reference_faces
from facefusion.face_analyser import get_average_face, get_many_faces
from facefusion.face_selector import sort_faces_by_order
from facefusion.face_store import clear_reference_faces, clear_static_faces, get_reference_faces
from facefusion.filesystem import filter_audio_paths, is_image, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.types import AudioFrame, Face, FaceSet, VisionFrame
from facefusion.uis.core import get_ui_component, get_ui_components, register_ui_component
from facefusion.uis.types import ComponentOptions
from facefusion.vision import count_video_frame_total, detect_frame_orientation, normalize_frame_color, read_static_image, read_static_images, read_video_frame, restrict_frame

PREVIEW_IMAGE : Optional[gradio.Image] = None
PREVIEW_FRAME_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global PREVIEW_IMAGE
	global PREVIEW_FRAME_SLIDER

	preview_image_options : ComponentOptions =\
	{
		'label': wording.get('uis.preview_image')
	}
	preview_frame_slider_options : ComponentOptions =\
	{
		'label': wording.get('uis.preview_frame_slider'),
		'step': 1,
		'minimum': 0,
		'maximum': 100,
		'visible': False
	}
	conditional_append_reference_faces()
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	source_frames = read_static_images(state_manager.get_item('source_paths'))
	source_faces = get_many_faces(source_frames)
	source_face = get_average_face(source_faces)
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	source_audio_frame = create_empty_audio_frame()

	if source_audio_path and state_manager.get_item('output_video_fps') and state_manager.get_item('reference_frame_number'):
		temp_audio_frame = get_audio_frame(source_audio_path, state_manager.get_item('output_video_fps'), state_manager.get_item('reference_frame_number'))
		if numpy.any(temp_audio_frame):
			source_audio_frame = temp_audio_frame

	if is_image(state_manager.get_item('target_path')):
		target_vision_frame = read_static_image(state_manager.get_item('target_path'))
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, target_vision_frame)
		preview_image_options['value'] = normalize_frame_color(preview_vision_frame)
		preview_image_options['elem_classes'] = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ]

	if is_video(state_manager.get_item('target_path')):
		temp_vision_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, temp_vision_frame)
		preview_image_options['value'] = normalize_frame_color(preview_vision_frame)
		preview_image_options['elem_classes'] = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ]
		preview_image_options['visible'] = True
		preview_frame_slider_options['value'] = state_manager.get_item('reference_frame_number')
		preview_frame_slider_options['maximum'] = count_video_frame_total(state_manager.get_item('target_path'))
		preview_frame_slider_options['visible'] = True
	PREVIEW_IMAGE = gradio.Image(**preview_image_options)
	PREVIEW_FRAME_SLIDER = gradio.Slider(**preview_frame_slider_options)
	register_ui_component('preview_frame_slider', PREVIEW_FRAME_SLIDER)


def listen() -> None:
	PREVIEW_FRAME_SLIDER.release(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE, show_progress = 'hidden')
	PREVIEW_FRAME_SLIDER.change(slide_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE, show_progress = 'hidden', trigger_mode = 'once')

	reference_face_position_gallery = get_ui_component('reference_face_position_gallery')
	if reference_face_position_gallery:
		reference_face_position_gallery.select(clear_and_update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'source_audio',
		'source_image',
		'target_image',
		'target_video'
	]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_frame_slider, outputs = PREVIEW_FRAME_SLIDER)

	for ui_component in get_ui_components(
	[
		'face_debugger_items_checkbox_group',
		'frame_colorizer_size_dropdown',
		'face_mask_types_checkbox_group',
		'face_mask_areas_checkbox_group',
		'face_mask_regions_checkbox_group'
	]):
		ui_component.change(update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'age_modifier_direction_slider',
		'deep_swapper_morph_slider',
		'expression_restorer_factor_slider',
		'face_editor_eyebrow_direction_slider',
		'face_editor_eye_gaze_horizontal_slider',
		'face_editor_eye_gaze_vertical_slider',
		'face_editor_eye_open_ratio_slider',
		'face_editor_lip_open_ratio_slider',
		'face_editor_mouth_grim_slider',
		'face_editor_mouth_pout_slider',
		'face_editor_mouth_purse_slider',
		'face_editor_mouth_smile_slider',
		'face_editor_mouth_position_horizontal_slider',
		'face_editor_mouth_position_vertical_slider',
		'face_editor_head_pitch_slider',
		'face_editor_head_yaw_slider',
		'face_editor_head_roll_slider',
		'face_enhancer_blend_slider',
		'face_enhancer_weight_slider',
		'frame_colorizer_blend_slider',
		'frame_enhancer_blend_slider',
		'lip_syncer_weight_slider',
		'reference_face_distance_slider',
		'face_selector_age_range_slider',
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
		'age_modifier_model_dropdown',
		'deep_swapper_model_dropdown',
		'expression_restorer_model_dropdown',
		'processors_checkbox_group',
		'face_editor_model_dropdown',
		'face_enhancer_model_dropdown',
		'face_swapper_model_dropdown',
		'face_swapper_pixel_boost_dropdown',
		'frame_colorizer_model_dropdown',
		'frame_enhancer_model_dropdown',
		'lip_syncer_model_dropdown',
		'face_selector_mode_dropdown',
		'face_selector_order_dropdown',
		'face_selector_gender_dropdown',
		'face_selector_race_dropdown',
		'face_detector_model_dropdown',
		'face_detector_size_dropdown',
		'face_detector_angles_checkbox_group',
		'face_landmarker_model_dropdown',
		'face_occluder_model_dropdown',
		'face_parser_model_dropdown'
	]):
		ui_component.change(clear_and_update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'face_detector_score_slider',
		'face_landmarker_score_slider'
	]):
		ui_component.release(clear_and_update_preview_image, inputs = PREVIEW_FRAME_SLIDER, outputs = PREVIEW_IMAGE)


def clear_and_update_preview_image(frame_number : int = 0) -> gradio.Image:
	clear_reference_faces()
	clear_static_faces()
	return update_preview_image(frame_number)


def slide_preview_image(frame_number : int = 0) -> gradio.Image:
	if is_video(state_manager.get_item('target_path')):
		preview_vision_frame = normalize_frame_color(read_video_frame(state_manager.get_item('target_path'), frame_number))
		preview_vision_frame = restrict_frame(preview_vision_frame, (1024, 1024))
		return gradio.Image(value = preview_vision_frame)
	return gradio.Image(value = None)


def update_preview_image(frame_number : int = 0) -> gradio.Image:
	while process_manager.is_checking():
		sleep(0.5)
	conditional_append_reference_faces()
	reference_faces = get_reference_faces() if 'reference' in state_manager.get_item('face_selector_mode') else None
	source_frames = read_static_images(state_manager.get_item('source_paths'))
	source_faces = []

	for source_frame in source_frames:
		temp_faces = get_many_faces([ source_frame ])
		temp_faces = sort_faces_by_order(temp_faces, 'large-small')
		if temp_faces:
			source_faces.append(get_first(temp_faces))
	source_face = get_average_face(source_faces)
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	source_audio_frame = create_empty_audio_frame()

	if source_audio_path and state_manager.get_item('output_video_fps') and state_manager.get_item('reference_frame_number'):
		reference_audio_frame_number = state_manager.get_item('reference_frame_number')
		if state_manager.get_item('trim_frame_start'):
			reference_audio_frame_number -= state_manager.get_item('trim_frame_start')
		temp_audio_frame = get_audio_frame(source_audio_path, state_manager.get_item('output_video_fps'), reference_audio_frame_number)
		if numpy.any(temp_audio_frame):
			source_audio_frame = temp_audio_frame

	if is_image(state_manager.get_item('target_path')):
		target_vision_frame = read_static_image(state_manager.get_item('target_path'))
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, target_vision_frame)
		preview_vision_frame = normalize_frame_color(preview_vision_frame)
		return gradio.Image(value = preview_vision_frame, elem_classes = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ])

	if is_video(state_manager.get_item('target_path')):
		temp_vision_frame = read_video_frame(state_manager.get_item('target_path'), frame_number)
		preview_vision_frame = process_preview_frame(reference_faces, source_face, source_audio_frame, temp_vision_frame)
		preview_vision_frame = normalize_frame_color(preview_vision_frame)
		return gradio.Image(value = preview_vision_frame, elem_classes = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ])
	return gradio.Image(value = None, elem_classes = None)


def update_preview_frame_slider() -> gradio.Slider:
	if is_video(state_manager.get_item('target_path')):
		video_frame_total = count_video_frame_total(state_manager.get_item('target_path'))
		return gradio.Slider(maximum = video_frame_total, visible = True)
	return gradio.Slider(value = 0, visible = False)


def process_preview_frame(reference_faces : FaceSet, source_face : Face, source_audio_frame : AudioFrame, target_vision_frame : VisionFrame) -> VisionFrame:
	target_vision_frame = restrict_frame(target_vision_frame, (1024, 1024))
	source_vision_frame = target_vision_frame.copy()
	if analyse_frame(target_vision_frame):
		return cv2.GaussianBlur(target_vision_frame, (99, 99), 0)

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()
		if processor_module.pre_process('preview'):
			target_vision_frame = processor_module.process_frame(
			{
				'reference_faces': reference_faces,
				'source_face': source_face,
				'source_audio_frame': source_audio_frame,
				'source_vision_frame': source_vision_frame,
				'target_vision_frame': target_vision_frame
			})
		logger.enable()
	return target_vision_frame
