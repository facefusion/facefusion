<<<<<<< HEAD
from typing import Tuple, Optional
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.face_store import clear_static_faces, clear_reference_faces
from facefusion.uis.typing import File
from facefusion.filesystem import get_file_size, is_image, is_video
from facefusion.uis.core import register_ui_component
=======
from typing import Optional, Tuple

import gradio

from facefusion import state_manager, wording
from facefusion.face_store import clear_reference_faces, clear_static_faces
from facefusion.filesystem import get_file_size, is_image, is_video
from facefusion.uis.core import register_ui_component
from facefusion.uis.typing import ComponentOptions, File
>>>>>>> origin/master
from facefusion.vision import get_video_frame, normalize_frame_color

FILE_SIZE_LIMIT = 512 * 1024 * 1024

TARGET_FILE : Optional[gradio.File] = None
TARGET_IMAGE : Optional[gradio.Image] = None
TARGET_VIDEO : Optional[gradio.Video] = None


def render() -> None:
	global TARGET_FILE
	global TARGET_IMAGE
	global TARGET_VIDEO

<<<<<<< HEAD
	is_target_image = is_image(facefusion.globals.target_path)
	is_target_video = is_video(facefusion.globals.target_path)
=======
	is_target_image = is_image(state_manager.get_item('target_path'))
	is_target_video = is_video(state_manager.get_item('target_path'))
>>>>>>> origin/master
	TARGET_FILE = gradio.File(
		label = wording.get('uis.target_file'),
		file_count = 'single',
		file_types =
		[
<<<<<<< HEAD
			'.png',
			'.jpg',
			'.webp',
			'.webm',
			'.mp4'
		],
		value = facefusion.globals.target_path if is_target_image or is_target_video else None
	)
	target_image_args =\
=======
			'image',
			'video'
		],
		value = state_manager.get_item('target_path') if is_target_image or is_target_video else None
	)
	target_image_options : ComponentOptions =\
>>>>>>> origin/master
	{
		'show_label': False,
		'visible': False
	}
<<<<<<< HEAD
	target_video_args =\
=======
	target_video_options : ComponentOptions =\
>>>>>>> origin/master
	{
		'show_label': False,
		'visible': False
	}
	if is_target_image:
<<<<<<< HEAD
		target_image_args['value'] = TARGET_FILE.value['name']
		target_image_args['visible'] = True
	if is_target_video:
		if get_file_size(facefusion.globals.target_path) > FILE_SIZE_LIMIT:
			preview_vision_frame = normalize_frame_color(get_video_frame(facefusion.globals.target_path))
			target_image_args['value'] = preview_vision_frame
			target_image_args['visible'] = True
		else:
			target_video_args['value'] = TARGET_FILE.value['name']
			target_video_args['visible'] = True
	TARGET_IMAGE = gradio.Image(**target_image_args)
	TARGET_VIDEO = gradio.Video(**target_video_args)
=======
		target_image_options['value'] = TARGET_FILE.value.get('path')
		target_image_options['visible'] = True
	if is_target_video:
		if get_file_size(state_manager.get_item('target_path')) > FILE_SIZE_LIMIT:
			preview_vision_frame = normalize_frame_color(get_video_frame(state_manager.get_item('target_path')))
			target_image_options['value'] = preview_vision_frame
			target_image_options['visible'] = True
		else:
			target_video_options['value'] = TARGET_FILE.value.get('path')
			target_video_options['visible'] = True
	TARGET_IMAGE = gradio.Image(**target_image_options)
	TARGET_VIDEO = gradio.Video(**target_video_options)
>>>>>>> origin/master
	register_ui_component('target_image', TARGET_IMAGE)
	register_ui_component('target_video', TARGET_VIDEO)


def listen() -> None:
	TARGET_FILE.change(update, inputs = TARGET_FILE, outputs = [ TARGET_IMAGE, TARGET_VIDEO ])


def update(file : File) -> Tuple[gradio.Image, gradio.Video]:
	clear_reference_faces()
	clear_static_faces()
	if file and is_image(file.name):
<<<<<<< HEAD
		facefusion.globals.target_path = file.name
		return gradio.Image(value = file.name, visible = True), gradio.Video(value = None, visible = False)
	if file and is_video(file.name):
		facefusion.globals.target_path = file.name
=======
		state_manager.set_item('target_path', file.name)
		return gradio.Image(value = file.name, visible = True), gradio.Video(value = None, visible = False)
	if file and is_video(file.name):
		state_manager.set_item('target_path', file.name)
>>>>>>> origin/master
		if get_file_size(file.name) > FILE_SIZE_LIMIT:
			preview_vision_frame = normalize_frame_color(get_video_frame(file.name))
			return gradio.Image(value = preview_vision_frame, visible = True), gradio.Video(value = None, visible = False)
		return gradio.Image(value = None, visible = False), gradio.Video(value = file.name, visible = True)
<<<<<<< HEAD
	facefusion.globals.target_path = None
=======
	state_manager.clear_item('target_path')
>>>>>>> origin/master
	return gradio.Image(value = None, visible = False), gradio.Video(value = None, visible = False)
