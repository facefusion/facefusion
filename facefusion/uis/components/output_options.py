from typing import Optional, Tuple

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.common_helper import calc_int_step
from facefusion.ffmpeg import get_available_encoder_set
from facefusion.filesystem import is_image, is_video
from facefusion.types import AudioEncoder, Fps, VideoEncoder, VideoPreset
from facefusion.uis.core import get_ui_components, register_ui_component
from facefusion.vision import create_image_resolutions, create_video_resolutions, detect_image_resolution, detect_video_fps, detect_video_resolution, pack_resolution

OUTPUT_IMAGE_QUALITY_SLIDER : Optional[gradio.Slider] = None
OUTPUT_IMAGE_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_AUDIO_ENCODER_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_AUDIO_QUALITY_SLIDER : Optional[gradio.Slider] = None
OUTPUT_AUDIO_VOLUME_SLIDER : Optional[gradio.Slider] = None
OUTPUT_VIDEO_ENCODER_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_PRESET_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_RESOLUTION_DROPDOWN : Optional[gradio.Dropdown] = None
OUTPUT_VIDEO_QUALITY_SLIDER : Optional[gradio.Slider] = None
OUTPUT_VIDEO_FPS_SLIDER : Optional[gradio.Slider] = None


def render() -> None:
	global OUTPUT_IMAGE_QUALITY_SLIDER
	global OUTPUT_IMAGE_RESOLUTION_DROPDOWN
	global OUTPUT_AUDIO_ENCODER_DROPDOWN
	global OUTPUT_AUDIO_QUALITY_SLIDER
	global OUTPUT_AUDIO_VOLUME_SLIDER
	global OUTPUT_VIDEO_ENCODER_DROPDOWN
	global OUTPUT_VIDEO_PRESET_DROPDOWN
	global OUTPUT_VIDEO_RESOLUTION_DROPDOWN
	global OUTPUT_VIDEO_QUALITY_SLIDER
	global OUTPUT_VIDEO_FPS_SLIDER

	output_image_resolutions = []
	output_video_resolutions = []
	available_encoder_set = get_available_encoder_set()
	if is_image(state_manager.get_item('target_path')):
		output_image_resolution = detect_image_resolution(state_manager.get_item('target_path'))
		output_image_resolutions = create_image_resolutions(output_image_resolution)
	if is_video(state_manager.get_item('target_path')):
		output_video_resolution = detect_video_resolution(state_manager.get_item('target_path'))
		output_video_resolutions = create_video_resolutions(output_video_resolution)
	OUTPUT_IMAGE_QUALITY_SLIDER = gradio.Slider(
		label = wording.get('uis.output_image_quality_slider'),
		value = state_manager.get_item('output_image_quality'),
		step = calc_int_step(facefusion.choices.output_image_quality_range),
		minimum = facefusion.choices.output_image_quality_range[0],
		maximum = facefusion.choices.output_image_quality_range[-1],
		visible = is_image(state_manager.get_item('target_path'))
	)
	OUTPUT_IMAGE_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_image_resolution_dropdown'),
		choices = output_image_resolutions,
		value = state_manager.get_item('output_image_resolution'),
		visible = is_image(state_manager.get_item('target_path'))
	)
	OUTPUT_AUDIO_ENCODER_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_audio_encoder_dropdown'),
		choices = available_encoder_set.get('audio'),
		value = state_manager.get_item('output_audio_encoder'),
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_AUDIO_QUALITY_SLIDER = gradio.Slider(
		label = wording.get('uis.output_audio_quality_slider'),
		value = state_manager.get_item('output_audio_quality'),
		step = calc_int_step(facefusion.choices.output_audio_quality_range),
		minimum = facefusion.choices.output_audio_quality_range[0],
		maximum = facefusion.choices.output_audio_quality_range[-1],
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_AUDIO_VOLUME_SLIDER = gradio.Slider(
		label = wording.get('uis.output_audio_volume_slider'),
		value = state_manager.get_item('output_audio_volume'),
		step = calc_int_step(facefusion.choices.output_audio_volume_range),
		minimum = facefusion.choices.output_audio_volume_range[0],
		maximum = facefusion.choices.output_audio_volume_range[-1],
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_VIDEO_ENCODER_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_encoder_dropdown'),
		choices = available_encoder_set.get('video'),
		value = state_manager.get_item('output_video_encoder'),
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_VIDEO_PRESET_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_preset_dropdown'),
		choices = facefusion.choices.output_video_presets,
		value = state_manager.get_item('output_video_preset'),
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_VIDEO_QUALITY_SLIDER = gradio.Slider(
		label = wording.get('uis.output_video_quality_slider'),
		value = state_manager.get_item('output_video_quality'),
		step = calc_int_step(facefusion.choices.output_video_quality_range),
		minimum = facefusion.choices.output_video_quality_range[0],
		maximum = facefusion.choices.output_video_quality_range[-1],
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_VIDEO_RESOLUTION_DROPDOWN = gradio.Dropdown(
		label = wording.get('uis.output_video_resolution_dropdown'),
		choices = output_video_resolutions,
		value = state_manager.get_item('output_video_resolution'),
		visible = is_video(state_manager.get_item('target_path'))
	)
	OUTPUT_VIDEO_FPS_SLIDER = gradio.Slider(
		label = wording.get('uis.output_video_fps_slider'),
		value = state_manager.get_item('output_video_fps'),
		step = 0.01,
		minimum = 1,
		maximum = 60,
		visible = is_video(state_manager.get_item('target_path'))
	)
	register_ui_component('output_video_fps_slider', OUTPUT_VIDEO_FPS_SLIDER)


def listen() -> None:
	OUTPUT_IMAGE_QUALITY_SLIDER.release(update_output_image_quality, inputs = OUTPUT_IMAGE_QUALITY_SLIDER)
	OUTPUT_IMAGE_RESOLUTION_DROPDOWN.change(update_output_image_resolution, inputs = OUTPUT_IMAGE_RESOLUTION_DROPDOWN)
	OUTPUT_AUDIO_ENCODER_DROPDOWN.change(update_output_audio_encoder, inputs = OUTPUT_AUDIO_ENCODER_DROPDOWN)
	OUTPUT_AUDIO_QUALITY_SLIDER.release(update_output_audio_quality, inputs = OUTPUT_AUDIO_QUALITY_SLIDER)
	OUTPUT_AUDIO_VOLUME_SLIDER.release(update_output_audio_volume, inputs = OUTPUT_AUDIO_VOLUME_SLIDER)
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
		for method in [ 'change', 'clear' ]:
			getattr(ui_component, method)(remote_update, outputs = [ OUTPUT_IMAGE_QUALITY_SLIDER, OUTPUT_IMAGE_RESOLUTION_DROPDOWN, OUTPUT_AUDIO_ENCODER_DROPDOWN, OUTPUT_AUDIO_QUALITY_SLIDER, OUTPUT_AUDIO_VOLUME_SLIDER, OUTPUT_VIDEO_ENCODER_DROPDOWN, OUTPUT_VIDEO_PRESET_DROPDOWN, OUTPUT_VIDEO_QUALITY_SLIDER, OUTPUT_VIDEO_RESOLUTION_DROPDOWN, OUTPUT_VIDEO_FPS_SLIDER ])


def remote_update() -> Tuple[gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Slider, gradio.Dropdown, gradio.Dropdown, gradio.Slider, gradio.Dropdown, gradio.Slider]:
	if is_image(state_manager.get_item('target_path')):
		output_image_resolution = detect_image_resolution(state_manager.get_item('target_path'))
		output_image_resolutions = create_image_resolutions(output_image_resolution)
		state_manager.set_item('output_image_resolution', pack_resolution(output_image_resolution))
		return gradio.Slider(visible = True), gradio.Dropdown(value = state_manager.get_item('output_image_resolution'), choices = output_image_resolutions, visible = True), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False)
	if is_video(state_manager.get_item('target_path')):
		output_video_resolution = detect_video_resolution(state_manager.get_item('target_path'))
		output_video_resolutions = create_video_resolutions(output_video_resolution)
		state_manager.set_item('output_video_resolution', pack_resolution(output_video_resolution))
		state_manager.set_item('output_video_fps', detect_video_fps(state_manager.get_item('target_path')))
		return gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = True), gradio.Slider(visible = True), gradio.Slider(visible = True), gradio.Dropdown(visible = True), gradio.Dropdown(visible = True), gradio.Slider(visible = True), gradio.Dropdown(value = state_manager.get_item('output_video_resolution'), choices = output_video_resolutions, visible = True), gradio.Slider(value = state_manager.get_item('output_video_fps'), visible = True)
	return gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False), gradio.Dropdown(visible = False), gradio.Slider(visible = False)


def update_output_image_quality(output_image_quality : float) -> None:
	state_manager.set_item('output_image_quality', int(output_image_quality))


def update_output_image_resolution(output_image_resolution : str) -> None:
	state_manager.set_item('output_image_resolution', output_image_resolution)


def update_output_audio_encoder(output_audio_encoder : AudioEncoder) -> None:
	state_manager.set_item('output_audio_encoder', output_audio_encoder)


def update_output_audio_quality(output_audio_quality : float) -> None:
	state_manager.set_item('output_audio_quality', int(output_audio_quality))


def update_output_audio_volume(output_audio_volume: float) -> None:
	state_manager.set_item('output_audio_volume', int(output_audio_volume))


def update_output_video_encoder(output_video_encoder : VideoEncoder) -> None:
	state_manager.set_item('output_video_encoder', output_video_encoder)


def update_output_video_preset(output_video_preset : VideoPreset) -> None:
	state_manager.set_item('output_video_preset', output_video_preset)


def update_output_video_quality(output_video_quality : float) -> None:
	state_manager.set_item('output_video_quality', int(output_video_quality))


def update_output_video_resolution(output_video_resolution : str) -> None:
	state_manager.set_item('output_video_resolution', output_video_resolution)


def update_output_video_fps(output_video_fps : Fps) -> None:
	state_manager.set_item('output_video_fps', output_video_fps)
