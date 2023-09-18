from typing import Optional, Generator, Deque
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import os
import platform
import subprocess
import cv2
import gradio
from tqdm import tqdm

import facefusion.globals
from facefusion import wording
from facefusion.typing import Frame, Face
from facefusion.face_analyser import get_one_face
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.uis import core as ui
from facefusion.uis.typing import StreamMode, WebcamMode, Update
from facefusion.utilities import open_ffmpeg
from facefusion.vision import normalize_frame_color, read_static_image

WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global WEBCAM_IMAGE
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('webcam_image_label')
	)
	WEBCAM_START_BUTTON = gradio.Button(
		value = wording.get('start_button_label'),
		variant = 'primary'
	)
	WEBCAM_STOP_BUTTON = gradio.Button(
		value = wording.get('stop_button_label')
	)


def listen() -> None:
	start_event = None
	webcam_mode_radio = ui.get_component('webcam_mode_radio')
	webcam_resolution_dropdown = ui.get_component('webcam_resolution_dropdown')
	webcam_fps_slider = ui.get_component('webcam_fps_slider')
	if webcam_mode_radio and webcam_resolution_dropdown and webcam_fps_slider:
		start_event = WEBCAM_START_BUTTON.click(start, inputs = [ webcam_mode_radio, webcam_resolution_dropdown, webcam_fps_slider ], outputs = WEBCAM_IMAGE)
		webcam_mode_radio.change(stop, outputs = WEBCAM_IMAGE, cancels = start_event)
		webcam_resolution_dropdown.change(stop, outputs = WEBCAM_IMAGE, cancels = start_event)
		webcam_fps_slider.change(stop, outputs = WEBCAM_IMAGE, cancels = start_event)
	WEBCAM_STOP_BUTTON.click(stop, cancels = start_event)
	source_image = ui.get_component('source_image')
	if source_image:
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(source_image, method)(stop, cancels = start_event)


def start(mode: WebcamMode, resolution: str, fps: float) -> Generator[Frame, None, None]:
	facefusion.globals.face_recognition = 'many'
	source_face = get_one_face(read_static_image(facefusion.globals.source_path))
	stream = None
	if mode == 'stream_udp':
		stream = open_stream('udp', resolution, fps)
	if mode == 'stream_v4l2':
		stream = open_stream('v4l2', resolution, fps)
	capture = capture_webcam(resolution, fps)
	if capture.isOpened():
		for capture_frame in multi_process_capture(source_face, capture):
			if stream is not None:
				stream.stdin.write(capture_frame.tobytes())
			yield normalize_frame_color(capture_frame)


def multi_process_capture(source_face: Face, capture : cv2.VideoCapture) -> Generator[Frame, None, None]:
	progress = tqdm(desc = wording.get('processing'), unit = 'frame', dynamic_ncols = True)
	with ThreadPoolExecutor(max_workers = facefusion.globals.execution_thread_count) as executor:
		futures = []
		deque_capture_frames : Deque[Frame] = deque()
		while True:
			_, capture_frame = capture.read()
			future = executor.submit(process_stream_frame, source_face, capture_frame)
			futures.append(future)
			for future_done in [ future for future in futures if future.done() ]:
				capture_frame = future_done.result()
				deque_capture_frames.append(capture_frame)
				futures.remove(future_done)
			while deque_capture_frames:
				yield deque_capture_frames.popleft()
				progress.update()


def stop() -> Update:
	return gradio.update(value = None)


def capture_webcam(resolution : str, fps : float) -> cv2.VideoCapture:
	width, height = resolution.split('x')
	if platform.system().lower() == 'windows':
		capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
	else:
		capture = cv2.VideoCapture(0)
	capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) # type: ignore[attr-defined]
	capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
	capture.set(cv2.CAP_PROP_FPS, fps)
	return capture


def process_stream_frame(source_face : Face, temp_frame : Frame) -> Frame:
	for frame_processor in facefusion.globals.frame_processors:
		frame_processor_module = load_frame_processor_module(frame_processor)
		if frame_processor_module.pre_process('stream'):
			temp_frame = frame_processor_module.process_frame(
				source_face,
				None,
				temp_frame
			)
	return temp_frame


def open_stream(mode : StreamMode, resolution : str, fps : float) -> subprocess.Popen[bytes]:
	commands = [ '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', resolution, '-r', str(fps), '-i', '-' ]
	if mode == 'udp':
		commands.extend([ '-b:v', '2000k', '-f', 'mpegts', 'udp://localhost:27000?pkt_size=1316' ])
	if mode == 'v4l2':
		device_name = os.listdir('/sys/devices/virtual/video4linux')[0]
		commands.extend([ '-f', 'v4l2', '/dev/' + device_name ])
	return open_ffmpeg(commands)
