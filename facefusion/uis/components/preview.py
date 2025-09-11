from time import sleep
from typing import List, Optional, Tuple

import cv2
import gradio
import numpy

from facefusion import logger, process_manager, state_manager, wording
from facefusion.audio import create_empty_audio_frame, get_voice_frame
from facefusion.common_helper import get_first
from facefusion.content_analyser import analyse_frame
from facefusion.face_analyser import get_one_face
from facefusion.face_selector import select_faces
from facefusion.face_store import clear_static_faces
from facefusion.filesystem import filter_audio_paths, is_image, is_video
from facefusion.processors.core import get_processors_modules
from facefusion.types import AudioFrame, Face, VisionFrame
from facefusion.uis import choices as uis_choices
from facefusion.uis.core import get_ui_component, get_ui_components, register_ui_component
from facefusion.uis.types import ComponentOptions, PreviewMode
from facefusion.vision import detect_frame_orientation, fit_cover_frame, obscure_frame, read_static_image, read_static_images, read_video_frame, restrict_frame, unpack_resolution

PREVIEW_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global PREVIEW_IMAGE

	preview_image_options : ComponentOptions =\
	{
		'label': wording.get('uis.preview_image')
	}

	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()

	if source_audio_path and state_manager.get_item('output_video_fps') and state_manager.get_item('reference_frame_number'):
		temp_voice_frame = get_voice_frame(source_audio_path, state_manager.get_item('output_video_fps'), state_manager.get_item('reference_frame_number'))
		if numpy.any(temp_voice_frame):
			source_voice_frame = temp_voice_frame

	if is_image(state_manager.get_item('target_path')):
		target_vision_frame = read_static_image(state_manager.get_item('target_path'))
		reference_vision_frame = read_static_image(state_manager.get_item('target_path'))
		preview_vision_frame = process_preview_frame(reference_vision_frame, source_vision_frames, source_audio_frame, source_voice_frame, target_vision_frame, uis_choices.preview_modes[0], uis_choices.preview_resolutions[-1])
		preview_image_options['value'] = cv2.cvtColor(preview_vision_frame, cv2.COLOR_BGR2RGB)
		preview_image_options['elem_classes'] = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ]

	if is_video(state_manager.get_item('target_path')):
		temp_vision_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		reference_vision_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		preview_vision_frame = process_preview_frame(reference_vision_frame, source_vision_frames, source_audio_frame, source_voice_frame, temp_vision_frame, uis_choices.preview_modes[0], uis_choices.preview_resolutions[-1])
		preview_image_options['value'] = cv2.cvtColor(preview_vision_frame, cv2.COLOR_BGR2RGB)
		preview_image_options['elem_classes'] = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ]
		preview_image_options['visible'] = True
	PREVIEW_IMAGE = gradio.Image(**preview_image_options)
	register_ui_component('preview_image', PREVIEW_IMAGE)


def listen() -> None:
	preview_frame_slider = get_ui_component('preview_frame_slider')
	preview_mode_dropdown = get_ui_component('preview_mode_dropdown')
	preview_resolution_dropdown = get_ui_component('preview_resolution_dropdown')

	if preview_mode_dropdown:
		preview_mode_dropdown.change(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

	if preview_resolution_dropdown:
		preview_resolution_dropdown.change(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

	if preview_frame_slider:
		preview_frame_slider.release(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE, show_progress = 'hidden')
		preview_frame_slider.change(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE, show_progress = 'hidden', trigger_mode = 'once')

		reference_face_position_gallery = get_ui_component('reference_face_position_gallery')
		if reference_face_position_gallery:
			reference_face_position_gallery.select(clear_and_update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'source_audio',
		'source_image',
		'target_image',
		'target_video'
	]):
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'face_debugger_items_checkbox_group',
		'frame_colorizer_size_dropdown',
		'face_mask_types_checkbox_group',
		'face_mask_areas_checkbox_group',
		'face_mask_regions_checkbox_group',
		'expression_restorer_areas_checkbox_group'
	]):
		ui_component.change(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

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
		'face_swapper_weight_slider',
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
		ui_component.release(update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

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
		'face_parser_model_dropdown',
		'voice_extractor_model_dropdown'
	]):
		ui_component.change(clear_and_update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)

	for ui_component in get_ui_components(
	[
		'face_detector_score_slider',
		'face_landmarker_score_slider'
	]):
		ui_component.release(clear_and_update_preview_image, inputs = [ preview_mode_dropdown, preview_resolution_dropdown, preview_frame_slider ], outputs = PREVIEW_IMAGE)


def update_preview_image(preview_mode : PreviewMode, preview_resolution : str, frame_number : int = 0) -> gradio.Image:
	while process_manager.is_checking():
		sleep(0.5)

	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_path = get_first(filter_audio_paths(state_manager.get_item('source_paths')))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()

	if source_audio_path and state_manager.get_item('output_video_fps') and state_manager.get_item('reference_frame_number'):
		reference_audio_frame_number = state_manager.get_item('reference_frame_number')
		if state_manager.get_item('trim_frame_start'):
			reference_audio_frame_number -= state_manager.get_item('trim_frame_start')
		temp_voice_frame = get_voice_frame(source_audio_path, state_manager.get_item('output_video_fps'), reference_audio_frame_number)
		if numpy.any(temp_voice_frame):
			source_voice_frame = temp_voice_frame

	if is_image(state_manager.get_item('target_path')):
		reference_vision_frame = read_static_image(state_manager.get_item('target_path'))
		target_vision_frame = read_static_image(state_manager.get_item('target_path'))
		preview_vision_frame = process_preview_frame(reference_vision_frame, source_vision_frames, source_audio_frame, source_voice_frame, target_vision_frame, preview_mode, preview_resolution)
		preview_vision_frame = cv2.cvtColor(preview_vision_frame, cv2.COLOR_BGR2RGB)
		return gradio.Image(value = preview_vision_frame, elem_classes = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ])

	if is_video(state_manager.get_item('target_path')):
		reference_vision_frame = read_video_frame(state_manager.get_item('target_path'), state_manager.get_item('reference_frame_number'))
		temp_vision_frame = read_video_frame(state_manager.get_item('target_path'), frame_number)
		preview_vision_frame = process_preview_frame(reference_vision_frame, source_vision_frames, source_audio_frame, source_voice_frame, temp_vision_frame, preview_mode, preview_resolution)
		preview_vision_frame = cv2.cvtColor(preview_vision_frame, cv2.COLOR_BGR2RGB)
		return gradio.Image(value = preview_vision_frame, elem_classes = [ 'image-preview', 'is-' + detect_frame_orientation(preview_vision_frame) ])
	return gradio.Image(value = None, elem_classes = None)


def clear_and_update_preview_image(preview_mode : PreviewMode, preview_resolution : str, frame_number : int = 0) -> gradio.Image:
	clear_static_faces()
	return update_preview_image(preview_mode, preview_resolution, frame_number)


def process_preview_frame(reference_vision_frame : VisionFrame, source_vision_frames : List[VisionFrame], source_audio_frame : AudioFrame, source_voice_frame : AudioFrame, target_vision_frame : VisionFrame, preview_mode : PreviewMode, preview_resolution : str) -> VisionFrame:
	target_vision_frame = restrict_frame(target_vision_frame, unpack_resolution(preview_resolution))
	temp_vision_frame = target_vision_frame.copy()

	if analyse_frame(target_vision_frame):
		if preview_mode == 'frame-by-frame':
			temp_vision_frame = obscure_frame(temp_vision_frame)
			return numpy.hstack((temp_vision_frame, temp_vision_frame))

		if preview_mode == 'face-by-face':
			target_crop_vision_frame, output_crop_vision_frame = create_face_by_face(reference_vision_frame, target_vision_frame, temp_vision_frame)
			target_crop_vision_frame = obscure_frame(target_crop_vision_frame)
			output_crop_vision_frame = obscure_frame(output_crop_vision_frame)
			return numpy.hstack((target_crop_vision_frame, output_crop_vision_frame))

		temp_vision_frame = obscure_frame(temp_vision_frame)
		return temp_vision_frame

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()
		if processor_module.pre_process('preview'):
			logger.enable()
			temp_vision_frame = processor_module.process_frame(
			{
				'reference_vision_frame': reference_vision_frame,
				'source_audio_frame': source_audio_frame,
				'source_voice_frame': source_voice_frame,
				'source_vision_frames': source_vision_frames,
				'target_vision_frame': target_vision_frame,
				'temp_vision_frame': temp_vision_frame
			})
		logger.enable()

	temp_vision_frame = cv2.resize(temp_vision_frame, target_vision_frame.shape[1::-1])

	if preview_mode == 'frame-by-frame':
		return numpy.hstack((target_vision_frame, temp_vision_frame))

	if preview_mode == 'face-by-face':
		target_crop_vision_frame, output_crop_vision_frame = create_face_by_face(reference_vision_frame, target_vision_frame, temp_vision_frame)
		return numpy.hstack((target_crop_vision_frame, output_crop_vision_frame))

	return temp_vision_frame


def create_face_by_face(reference_vision_frame : VisionFrame, target_vision_frame : VisionFrame, temp_vision_frame : VisionFrame) -> Tuple[VisionFrame, VisionFrame]:
	target_faces = select_faces(reference_vision_frame, target_vision_frame)
	target_face = get_one_face(target_faces)

	if target_face:
		target_crop_vision_frame = extract_crop_frame(target_vision_frame, target_face)
		output_crop_vision_frame = extract_crop_frame(temp_vision_frame, target_face)

		if numpy.any(target_crop_vision_frame) and numpy.any(output_crop_vision_frame):
			target_crop_dimension = min(target_crop_vision_frame.shape[:2])
			target_crop_vision_frame = fit_cover_frame(target_crop_vision_frame, (target_crop_dimension, target_crop_dimension))
			output_crop_vision_frame = fit_cover_frame(output_crop_vision_frame, (target_crop_dimension, target_crop_dimension))
			return target_crop_vision_frame, output_crop_vision_frame

	empty_vision_frame = numpy.zeros((512, 512, 3), dtype = numpy.uint8)
	return empty_vision_frame, empty_vision_frame


def extract_crop_frame(vision_frame : VisionFrame, face : Face) -> Optional[VisionFrame]:
	start_x, start_y, end_x, end_y = map(int, face.bounding_box)
	padding_x = int((end_x - start_x) * 0.25)
	padding_y = int((end_y - start_y) * 0.25)
	start_x = max(0, start_x - padding_x)
	start_y = max(0, start_y - padding_y)
	end_x = max(0, end_x + padding_x)
	end_y = max(0, end_y + padding_y)
	crop_vision_frame = vision_frame[start_y:end_y, start_x:end_x]
	return crop_vision_frame
