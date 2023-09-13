from typing import Optional, Generator
import os
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
from facefusion.vision import normalize_frame_color, read_image

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
	if webcam_mode_radio:
		start_event = WEBCAM_START_BUTTON.click(start, inputs = webcam_mode_radio, outputs = WEBCAM_IMAGE)
		webcam_mode_radio.change(update, outputs = WEBCAM_IMAGE, cancels = start_event)
	WEBCAM_STOP_BUTTON.click(None, cancels = start_event)
	source_image = ui.get_component('source_image')
	if source_image:
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(source_image, method)(None, cancels = start_event)


def update() -> Update:
	return gradio.update(value = None)


def start(mode : WebcamMode) -> Generator[Frame, None, None]:
	facefusion.globals.face_recognition = 'many'
	source_face = get_one_face(read_image(facefusion.globals.source_path))
	stream = None
	if mode == 'stream_udp':
		stream = open_stream('udp')
	if mode == 'stream_v4l2':
		stream = open_stream('v4l2')
	capture = capture_webcam()
	if capture.isOpened():
		progress = tqdm(desc = wording.get('processing'), unit = 'frame', dynamic_ncols = True)
		while True:
			_, temp_frame = capture.read()
			temp_frame = process_stream_frame(source_face, temp_frame)
			if temp_frame is not None:
				if stream is not None:
					stream.stdin.write(temp_frame.tobytes())
				yield normalize_frame_color(temp_frame)
				progress.update(1)


def capture_webcam(webcam_id : int = 0) -> cv2.VideoCapture:
	capture = cv2.VideoCapture(webcam_id)
	capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) # type: ignore[attr-defined]
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


def open_stream(mode : StreamMode) -> subprocess.Popen[bytes]:
	commands = [ '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '640x480', '-r', '30', '-i', '-' ]
	if mode == 'udp':
		commands.extend([ '-b:v', '2000k', '-f', 'mpegts', 'udp://localhost:27000?pkt_size=1316' ])
	if mode == 'v4l2':
		device_name = os.listdir('/sys/devices/virtual/video4linux')[0]
		commands.extend([ '-f', 'v4l2', '/dev/' + device_name ])
	return open_ffmpeg(commands)
