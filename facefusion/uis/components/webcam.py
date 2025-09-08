from typing import Generator, List, Optional, Tuple

import cv2
import gradio

from facefusion import state_manager, wording
from facefusion.camera_manager import clear_camera_pool, get_local_camera_capture
from facefusion.filesystem import has_image
from facefusion.streamer import multi_process_capture, open_stream
from facefusion.types import Fps, VisionFrame, WebcamMode
from facefusion.uis.core import get_ui_component
from facefusion.uis.types import File
from facefusion.vision import unpack_resolution

SOURCE_FILE : Optional[gradio.File] = None
WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global SOURCE_FILE
	global WEBCAM_IMAGE
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	has_source_image = has_image(state_manager.get_item('source_paths'))
	SOURCE_FILE = gradio.File(
		label = wording.get('uis.source_file'),
		file_count = 'multiple',
		value = state_manager.get_item('source_paths') if has_source_image else None
	)
	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('uis.webcam_image'),
		format = 'jpeg',
		visible = False
	)
	WEBCAM_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	WEBCAM_STOP_BUTTON = gradio.Button(
		value = wording.get('uis.stop_button'),
		size = 'sm',
		visible = False
	)


def listen() -> None:
	SOURCE_FILE.change(update_source, inputs = SOURCE_FILE, outputs = SOURCE_FILE)
	webcam_device_id_dropdown = get_ui_component('webcam_device_id_dropdown')
	webcam_mode_radio = get_ui_component('webcam_mode_radio')
	webcam_resolution_dropdown = get_ui_component('webcam_resolution_dropdown')
	webcam_fps_slider = get_ui_component('webcam_fps_slider')

	if webcam_device_id_dropdown and webcam_mode_radio and webcam_resolution_dropdown and webcam_fps_slider:
		WEBCAM_START_BUTTON.click(pre_start, outputs = [ SOURCE_FILE, WEBCAM_IMAGE, WEBCAM_START_BUTTON, WEBCAM_STOP_BUTTON ])
		start_event = WEBCAM_START_BUTTON.click(start, inputs = [ webcam_device_id_dropdown, webcam_mode_radio, webcam_resolution_dropdown, webcam_fps_slider ], outputs = WEBCAM_IMAGE)
		start_event.then(pre_stop)
		WEBCAM_STOP_BUTTON.click(stop, cancels = start_event, outputs = WEBCAM_IMAGE)
		WEBCAM_STOP_BUTTON.click(pre_stop, outputs = [ SOURCE_FILE, WEBCAM_IMAGE, WEBCAM_START_BUTTON, WEBCAM_STOP_BUTTON ])


def update_source(files : List[File]) -> gradio.File:
	file_names = [ file.name for file in files ] if files else None
	has_source_image = has_image(file_names)

	if has_source_image:
		state_manager.set_item('source_paths', file_names)
		return gradio.File(value = file_names)

	state_manager.clear_item('source_paths')
	return gradio.File(value = None)


def pre_start() -> Tuple[gradio.File, gradio.Image, gradio.Button, gradio.Button]:
	return gradio.File(visible = False), gradio.Image(visible = True), gradio.Button(visible = False), gradio.Button(visible = True)


def pre_stop() -> Tuple[gradio.File, gradio.Image, gradio.Button, gradio.Button]:
	return gradio.File(visible = True), gradio.Image(visible = False), gradio.Button(visible = True), gradio.Button(visible = False)


def start(webcam_device_id : int, webcam_mode : WebcamMode, webcam_resolution : str, webcam_fps : Fps) -> Generator[VisionFrame, None, None]:
	state_manager.init_item('face_selector_mode', 'one')
	state_manager.sync_state()

	camera_capture = get_local_camera_capture(webcam_device_id)
	stream = None

	if webcam_mode in [ 'udp', 'v4l2' ]:
		stream = open_stream(webcam_mode, webcam_resolution, webcam_fps) # type:ignore[arg-type]
	webcam_width, webcam_height = unpack_resolution(webcam_resolution)

	if camera_capture and camera_capture.isOpened():
		camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, webcam_width)
		camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, webcam_height)
		camera_capture.set(cv2.CAP_PROP_FPS, webcam_fps)

		for capture_frame in multi_process_capture(camera_capture, webcam_fps):
			capture_frame = cv2.cvtColor(capture_frame, cv2.COLOR_BGR2RGB)

			if webcam_mode == 'inline':
				yield capture_frame
			else:
				try:
					stream.stdin.write(capture_frame.tobytes())
				except Exception:
					pass


def stop() -> gradio.Image:
	clear_camera_pool()
	return gradio.Image(value = None)
