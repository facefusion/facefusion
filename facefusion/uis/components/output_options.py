from typing import Optional, Tuple
import gradio

import facefusion.globals
import facefusion.choices
from facefusion import wording
from facefusion.typing import OutputVideoEncoder, OutputVideoPreset, Fps
from facefusion.filesystem import is_image, is_video
from facefusion.uis.core import get_ui_components, register_ui_component
from facefusion.vision import detect_image_resolution, create_image_resolutions, detect_video_fps, detect_video_resolution, create_video_resolutions, pack_resolution

OUTPUT_PATH_TEXTBOX : Optional[gradio.Textbox] = None
OUTPUT_IMAGE_QUALITY_SLIDER : Optional[gradio.Slider] = None
OUTPUT_IMAGE_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_ENCODER_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_PRESET_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_QUALITY_SLIDER : Optional[gradio.Slider] = None
OUTPUT_VIDEO_FPS_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global OUTPUT_PATH_TEXTBOX
	global OUTPUT_IMAGE_QUALITY_SLIDER
	global OUTPUT_IMAGE_RESOLUTION_DROPDOWN
	global OUTPUT_VIDEO_ENCODER_DROPDOWN
	global OUTPUT_VIDEO_PRESET_DROPDOWN
	global OUTPUT_VIDEO_RESOLUTION_DROPDOWN
	global OUTPUT_VIDEO_QUALITY_SLIDER
	global OUTPUT_VIDEO_FPS_SLIDER

	output_image_resolutions = []
	output_video_resolutions = []
	if is_image(facefusion.globals.target_path):
		output_image_resolution = detect_image_resolution(facefusion.globals.target_path)
		output_image_resolutions = create_image_resolutions(output_image_resolution)
	if is_video(facefusion.globals.target_path):
		output_video_resolution = detect_video_resolution(facefusion.globals.target_path)
		output_video_resolutions = create_video_resolutions(output_video_resolution)
	facefusion.globals.output_path = facefusion.globals.output_path or '.'
	OUTPUT_PATH_TEXTBOX = gradio.Textbox(
		label = wording.get('uis.output_path_textbox'),
		value = facefusion.globals.output_path,
		max_lines = 1
	)
	OUTPUT_IMAGE_QUALITY_SLIDER = gradio.Slider(
		label = wording.get('uis.output_image_quality_slider'),
		value = facefusion.globals.output_image_quality,
		step = facefusion.choices.output_image_quality_range[1] - facefusion.choices.output_image_quality_range[0],
		minimum = facefusion.choices.output_image_quality_range[0],
		maximum = facefusion.choices.output_image_quality_range[-1],
		visible = is_image(facefusion.globals.target_path)
	)
	OUTPUT_IMAGE_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_image_resolution_dropdown'),
		choices = output_image_resolutions,
		value = facefusion.globals.output_image_resolution,
		visible = is_image(facefusion.globals.target_path)
	)
	OUTPUT_VIDEO_ENCODER_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_encoder_dropdown'),
		choices = facefusion.choices.output_video_encoders,
		value = facefusion.globals.output_video_encoder,
		visible = is_video(facefusion.globals.target_path)
	)
	OUTPUT_VIDEO_PRESET_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_preset_dropdown'),
		choices = facefusion.choices.output_video_presets,
		value = facefusion.globals.output_video_preset,
		visible = is_video(facefusion.globals.target_path)
	)
	OUTPUT_VIDEO_QUALITY_SLIDER = gradio.Slider(
		label = wording.get('uis.output_video_quality_slider'),
		value = facefusion.globals.output_video_quality,
		step = facefusion.choices.output_video_quality_range[1] - facefusion.choices.output_video_quality_range[0],
		minimum = facefusion.choices.output_video_quality_range[0],
		maximum = facefusion.choices.output_video_quality_range[-1],
		visible = is_video(facefusion.globals.target_path)
	)
	OUTPUT_VIDEO_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_resolution_dropdown'),
		choices = output_video_resolutions,
		value = facefusion.globals.output_video_resolution,
		visible = is_video(facefusion.globals.target_path)
	)
	OUTPUT_VIDEO_FPS_SLIDER = gradio.Slider(
		label = wording.get('uis.output_video_fps_slider'),
		value = facefusion.globals.output_video_fps,
		step = 0.01,
		minimum = 1,
		maximum = 60,
		visible = is_video(facefusion.globals.target_path)
	)
	register_ui_component('output_path_textbox', OUTPUT_PATH_TEXTBOX)
	register_ui_component('output_video_fps_slider', OUTPUT_VIDEO_FPS_SLIDER)


def listen() -> None:
	OUTPUT_PATH_TEXTBOX.change(update_output_path, inputs = OUTPUT_PATH_TEXTBOX)
	OUTPUT_IMAGE_QUALITY_SLIDER.release(update_output_image_quality, inputs = OUTPUT_IMAGE_QUALITY_SLIDER)
	OUTPUT_IMAGE_RESOLUTION_DROPDOWN.change(update_output_image_resolution, inputs = OUTPUT_IMAGE_RESOLUTION_DROPDOWN)
	OUTPUT_VIDEO_ENCODER_DROPDOWN.change(update_output_video_encoder, inputs = OUTPUT_VIDEO_ENCODER_DROPDOWN)
	OUTPUT_VIDEO_PRESET_DROPDOWN.change(update_output_video_preset, inputs = OUTPUT_VIDEO_PRESET_DROPDOWN)
	OUTPUT_VIDEO_QUALITY_SLIDER.release(update_output_video_quality, inputs = OUTPUT_VIDEO_QUALITY_SLIDER)
	OUTPUT_VIDEO_RESOLUTION_DROPDOWN.change(update_output_video_resolution, inputs = OUTPUT_VIDEO_RESOLUTION_DROPDOWN)
	OUTPUT_VIDEO_FPS_SLIDER.release(update_output_video_fps, inputs = OUTPUT_VIDEO_FPS_SLIDER)

	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(ui_component, method)(remote_update, outputs = [ OUTPUT_IMAGE_QUALITY_SLIDER, OUTPUT_IMAGE_RESOLUTION_DROPDOWN, OUTPUT_VIDEO_ENCODER_DROPDOWN, OUTPUT_VIDEO_PRESET_DROPDOWN, OUTPUT_VIDEO_QUALITY_SLIDER, OUTPUT_VIDEO_RESOLUTION_DROPDOWN, OUTPUT_VIDEO_FPS_SLIDER ])


def remote_update() -> Tuple[gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Slider]:
	if is_image(facefusion.globals.target_path):
		output_image_resolution = detect_image_resolution(facefusion.globals.target_path)
		output_image_resolutions = create_image_resolutions(output_image_resolution)
		facefusion.globals.output_image_resolution = pack_resolution(output_image_resolution)
		return gradio.Slider(visible = True), gradio.Dropdown(visible = True, value = facefusion.globals.output_image_resolution, choices = output_image_resolutions), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False, value = None, choices = None), gradio.Slider(visible = False, value = None)
	if is_video(facefusion.globals.target_path):
		output_video_resolution = detect_video_resolution(facefusion.globals.target_path)
		output_video_resolutions = create_video_resolutions(output_video_resolution)
		facefusion.globals.output_video_resolution = pack_resolution(output_video_resolution)
		facefusion.globals.output_video_fps = detect_video_fps(facefusion.globals.target_path)
		return gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = True), gradio.Dropdown(visible = True), gradio.Slider(visible = True), gradio.Dropdown(visible = True, value = facefusion.globals.output_video_resolution, choices = output_video_resolutions), gradio.Slider(visible = True, value = facefusion.globals.output_video_fps)
	return gradio.Slider(visible = False), gradio.Dropdown(visible = False, value = None, choices = None), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False, value = None, choices = None), gradio.Slider(visible = False, value = None)


def update_output_path(output_path : str) -> None:
	facefusion.globals.output_path = output_path


def update_output_image_quality(output_image_quality : int) -> None:
	facefusion.globals.output_image_quality = output_image_quality


def update_output_image_resolution(output_image_resolution : str) -> None:
	facefusion.globals.output_image_resolution = output_image_resolution


def update_output_video_encoder(output_video_encoder: OutputVideoEncoder) -> None:
	facefusion.globals.output_video_encoder = output_video_encoder


def update_output_video_preset(output_video_preset : OutputVideoPreset) -> None:
	facefusion.globals.output_video_preset = output_video_preset


def update_output_video_quality(output_video_quality : int) -> None:
	facefusion.globals.output_video_quality = output_video_quality


def update_output_video_resolution(output_video_resolution : str) -> None:
	facefusion.globals.output_video_resolution = output_video_resolution


def update_output_video_fps(output_video_fps : Fps) -> None:
	facefusion.globals.output_video_fps = output_video_fps
