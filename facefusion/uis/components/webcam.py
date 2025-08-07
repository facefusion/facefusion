import os
import subprocess
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Deque, Generator, Optional

import cv2
import gradio
from tqdm import tqdm

from facefusion import ffmpeg_builder, logger, state_manager, wording
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_stream
from facefusion.ffmpeg import open_ffmpeg
from facefusion.filesystem import is_directory
from facefusion.processors.core import get_processors_modules
from facefusion.types import Fps, StreamMode, VisionFrame, WebcamMode
from facefusion.uis.core import get_ui_component
from facefusion.vision import normalize_frame_color, read_static_images, unpack_resolution
from facefusion.camera_manager import clear_camera_pool, get_local_camera_capture

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
	state_manager.set_item('face_selector_mode', 'one')
	stream = None
	camera_capture = None

	if webcam_mode in [ 'udp', 'v4l2' ]:
		stream = open_stream(webcam_mode, webcam_resolution, webcam_fps) #type:ignore[arg-type]
	webcam_width, webcam_height = unpack_resolution(webcam_resolution)

	if isinstance(webcam_device_id, int):
		camera_capture = get_local_camera_capture(webcam_device_id)

	if camera_capture and camera_capture.isOpened():
		camera_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) #type:ignore[attr-defined]
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
				yield None


def multi_process_capture(camera_capture : cv2.VideoCapture, webcam_fps : Fps) -> Generator[VisionFrame, None, None]:
	capture_deque : Deque[VisionFrame] = deque()

	with tqdm(desc = wording.get('streaming'), unit = 'frame', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
			futures = []

			while camera_capture and camera_capture.isOpened():
				_, capture_frame = camera_capture.read()
				if analyse_stream(capture_frame, webcam_fps):
					yield None

				future = executor.submit(process_stream_frame, capture_frame)
				futures.append(future)

				for future_done in [ future for future in futures if future.done() ]:
					capture_frame = future_done.result()
					capture_deque.append(capture_frame)
					futures.remove(future_done)

				while capture_deque:
					progress.update()
					yield capture_deque.popleft()


def stop() -> gradio.Image:
	clear_camera_pool()
	return gradio.Image(value = None)


def process_stream_frame(target_vision_frame : VisionFrame) -> VisionFrame:
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	temp_vision_frame = target_vision_frame.copy()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()

		if processor_module.pre_process('stream'):
			temp_vision_frame = processor_module.process_frame(
			{
				'source_vision_frames': source_vision_frames,
				'source_audio_frame': source_audio_frame,
				'source_voice_frame': source_voice_frame,
				'target_vision_frame': target_vision_frame,
				'temp_vision_frame': temp_vision_frame
			})

		logger.enable()
	return temp_vision_frame


def open_stream(stream_mode : StreamMode, stream_resolution : str, stream_fps : Fps) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(stream_resolution),
		ffmpeg_builder.set_input_fps(stream_fps)
	)

	if stream_mode == 'udp':
		commands.extend(ffmpeg_builder.set_input('-'))
		commands.extend(ffmpeg_builder.set_stream_mode('udp'))
		commands.extend(ffmpeg_builder.set_stream_quality(2000))
		commands.extend(ffmpeg_builder.set_output('udp://localhost:27000?pkt_size=1316'))

	if stream_mode == 'v4l2':
		device_directory_path = '/sys/devices/virtual/video4linux'
		commands.extend(ffmpeg_builder.set_input('-'))
		commands.extend(ffmpeg_builder.set_stream_mode('v4l2'))

		if is_directory(device_directory_path):
			device_names = os.listdir(device_directory_path)

			for device_name in device_names:
				device_path = '/dev/' + device_name
				commands.extend(ffmpeg_builder.set_output(device_path))

		else:
			logger.error(wording.get('stream_not_loaded').format(stream_mode = stream_mode), __name__)

	return open_ffmpeg(commands)
