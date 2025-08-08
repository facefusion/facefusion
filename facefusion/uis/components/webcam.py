from typing import Generator, Optional

import cv2
import gradio

from facefusion import state_manager, wording
from facefusion.camera_manager import clear_camera_pool, get_local_camera_capture
from facefusion.streamer import multi_process_capture, open_stream
from facefusion.types import Fps, VisionFrame, WebcamMode
from facefusion.uis.core import get_ui_component
from facefusion.vision import normalize_frame_color, unpack_resolution

WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global WEBCAM_IMAGE
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('uis.webcam_image'),
		format = 'jpeg'
	)
	WEBCAM_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	WEBCAM_STOP_BUTTON = gradio.Button(
		value = wording.get('uis.stop_button'),
		size = 'sm'
	)


def listen() -> None:
	webcam_device_id_dropdown = get_ui_component('webcam_device_id_dropdown')
	webcam_mode_radio = get_ui_component('webcam_mode_radio')
	webcam_resolution_dropdown = get_ui_component('webcam_resolution_dropdown')
	webcam_fps_slider = get_ui_component('webcam_fps_slider')
	source_image = get_ui_component('source_image')

	if webcam_device_id_dropdown and webcam_mode_radio and webcam_resolution_dropdown and webcam_fps_slider:
		start_event = WEBCAM_START_BUTTON.click(start, inputs = [ webcam_device_id_dropdown, webcam_mode_radio, webcam_resolution_dropdown, webcam_fps_slider ], outputs = WEBCAM_IMAGE)
		WEBCAM_STOP_BUTTON.click(stop, cancels = start_event, outputs = WEBCAM_IMAGE)

	if source_image:
		source_image.change(stop, cancels = start_event, outputs = WEBCAM_IMAGE)


def start(webcam_device_id : int, webcam_mode : WebcamMode, webcam_resolution : str, webcam_fps : Fps) -> Generator[VisionFrame, None, None]:
	state_manager.init_item('face_selector_mode', 'one')
	camera_capture = get_local_camera_capture(webcam_device_id)
	stream = None

	if webcam_mode in [ 'udp', 'v4l2' ]:
		stream = open_stream(webcam_mode, webcam_resolution, webcam_fps) #type:ignore[arg-type]
	webcam_width, webcam_height = unpack_resolution(webcam_resolution)

	if camera_capture and camera_capture.isOpened():
		camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, webcam_width)
		camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, webcam_height)
		camera_capture.set(cv2.CAP_PROP_FPS, webcam_fps)

		for capture_frame in multi_process_capture(camera_capture, webcam_fps):
			capture_frame = normalize_frame_color(capture_frame)

			if webcam_mode == 'inline':
				yield capture_frame
			else:
				try:
					stream.stdin.write(capture_frame.tobytes())
				except Exception:
					clear_camera_pool()


def stop() -> gradio.Image:
	clear_camera_pool()
	return gradio.Image(value = None)
