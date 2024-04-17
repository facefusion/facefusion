from typing import Optional, Generator, Deque
import os
import platform
import subprocess
import cv2
import gradio
from time import sleep
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from tqdm import tqdm

import facefusion.globals
from facefusion import logger, wording
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_stream
from facefusion.filesystem import filter_image_paths
from facefusion.typing import VisionFrame, Face, Fps
from facefusion.face_analyser import get_average_face
from facefusion.processors.frame.core import get_frame_processors_modules, load_frame_processor_module
from facefusion.ffmpeg import open_ffmpeg
from facefusion.vision import normalize_frame_color, read_static_images, unpack_resolution
from facefusion.uis.typing import StreamMode, WebcamMode, Update
from facefusion.uis.core import get_ui_component, get_ui_components

WEBCAM_CAPTURE : Optional[cv2.VideoCapture] = None
WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def get_webcam_capture() -> Optional[cv2.VideoCapture]:
	global WEBCAM_CAPTURE

	if WEBCAM_CAPTURE is None:
		if platform.system().lower() == 'windows':
			webcam_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
		else:
			webcam_capture = cv2.VideoCapture(0)
		if webcam_capture and webcam_capture.isOpened():
			WEBCAM_CAPTURE = webcam_capture
	return WEBCAM_CAPTURE


def clear_webcam_capture() -> None:
	global WEBCAM_CAPTURE

	if WEBCAM_CAPTURE:
		WEBCAM_CAPTURE.release()
	WEBCAM_CAPTURE = None


def render() -> None:
	global WEBCAM_IMAGE
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('uis.webcam_image')
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
	start_event = None
	webcam_mode_radio = get_ui_component('webcam_mode_radio')
	webcam_resolution_dropdown = get_ui_component('webcam_resolution_dropdown')
	webcam_fps_slider = get_ui_component('webcam_fps_slider')
	if webcam_mode_radio and webcam_resolution_dropdown and webcam_fps_slider:
		start_event = WEBCAM_START_BUTTON.click(start, inputs = [ webcam_mode_radio, webcam_resolution_dropdown, webcam_fps_slider ], outputs = WEBCAM_IMAGE)
	WEBCAM_STOP_BUTTON.click(stop, cancels = start_event)

	for ui_component in get_ui_components(
	[
		'frame_processors_checkbox_group',
		'face_swapper_model_dropdown',
		'face_enhancer_model_dropdown',
		'frame_enhancer_model_dropdown',
		'lip_syncer_model_dropdown',
		'source_image'
	]):
		ui_component.change(update, cancels = start_event)


def start(webcam_mode : WebcamMode, webcam_resolution : str, webcam_fps : Fps) -> Generator[VisionFrame, None, None]:
	facefusion.globals.face_selector_mode = 'one'
	facefusion.globals.face_analyser_order = 'large-small'
	source_image_paths = filter_image_paths(facefusion.globals.source_paths)
	source_frames = read_static_images(source_image_paths)
	source_face = get_average_face(source_frames)
	stream = None

	if webcam_mode in [ 'udp', 'v4l2' ]:
		stream = open_stream(webcam_mode, webcam_resolution, webcam_fps) # type: ignore[arg-type]
	webcam_width, webcam_height = unpack_resolution(webcam_resolution)
	webcam_capture = get_webcam_capture()
	if webcam_capture and webcam_capture.isOpened():
		webcam_capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) # type: ignore[attr-defined]
		webcam_capture.set(cv2.CAP_PROP_FRAME_WIDTH, webcam_width)
		webcam_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, webcam_height)
		webcam_capture.set(cv2.CAP_PROP_FPS, webcam_fps)
		for capture_frame in multi_process_capture(source_face, webcam_capture, webcam_fps):
			if webcam_mode == 'inline':
				yield normalize_frame_color(capture_frame)
			else:
				try:
					stream.stdin.write(capture_frame.tobytes())
				except Exception:
					clear_webcam_capture()
				yield None


def multi_process_capture(source_face : Face, webcam_capture : cv2.VideoCapture, webcam_fps : Fps) -> Generator[VisionFrame, None, None]:
	with tqdm(desc = wording.get('processing'), unit = 'frame', ascii = ' =', disable = facefusion.globals.log_level in [ 'warn', 'error' ]) as progress:
		with ThreadPoolExecutor(max_workers = facefusion.globals.execution_thread_count) as executor:
			futures = []
			deque_capture_frames : Deque[VisionFrame] = deque()
			while webcam_capture and webcam_capture.isOpened():
				_, capture_frame = webcam_capture.read()
				if analyse_stream(capture_frame, webcam_fps):
					return
				future = executor.submit(process_stream_frame, source_face, capture_frame)
				futures.append(future)
				for future_done in [ future for future in futures if future.done() ]:
					capture_frame = future_done.result()
					deque_capture_frames.append(capture_frame)
					futures.remove(future_done)
				while deque_capture_frames:
					progress.update()
					yield deque_capture_frames.popleft()


def update() -> None:
	for frame_processor in facefusion.globals.frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		while not frame_processor_module.post_check():
			logger.disable()
			sleep(0.5)
		logger.enable()


def stop() -> Update:
	clear_webcam_capture()
	return gradio.update(value = None)


def process_stream_frame(source_face : Face, target_vision_frame : VisionFrame) -> VisionFrame:
	source_audio_frame = create_empty_audio_frame()
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		logger.disable()
		if frame_processor_module.pre_process('stream'):
			logger.enable()
			target_vision_frame = frame_processor_module.process_frame(
			{
				'source_face': source_face,
				'source_audio_frame': source_audio_frame,
				'target_vision_frame': target_vision_frame
			})
	return target_vision_frame


def open_stream(stream_mode : StreamMode, stream_resolution : str, stream_fps : Fps) -> subprocess.Popen[bytes]:
	commands = [ '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', stream_resolution, '-r', str(stream_fps), '-i', '-']
	if stream_mode == 'udp':
		commands.extend([ '-b:v', '2000k', '-f', 'mpegts', 'udp://localhost:27000?pkt_size=1316' ])
	if stream_mode == 'v4l2':
		try:
			device_name = os.listdir('/sys/devices/virtual/video4linux')[0]
			if device_name:
				commands.extend([ '-f', 'v4l2', '/dev/' + device_name ])
		except FileNotFoundError:
			logger.error(wording.get('stream_not_loaded').format(stream_mode = stream_mode), __name__.upper())
	return open_ffmpeg(commands)
