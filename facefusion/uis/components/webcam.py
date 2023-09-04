from typing import Optional, Generator
import os
import subprocess
import cv2
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.typing import Frame
from facefusion.face_analyser import get_one_face
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.uis.typing import StreamMode, WebcamMode, Update
from facefusion.utilities import open_ffmpeg
from facefusion.vision import normalize_frame_color

WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_MODE_RADIO : Optional[gradio.Radio] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global WEBCAM_IMAGE
	global WEBCAM_MODE_RADIO
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('webcam_image_label')
	)
	WEBCAM_MODE_RADIO = gradio.Radio(
		label = wording.get('webcam_mode_radio_label'),
		choices = [ 'inline', 'stream_udp', 'stream_v4l2' ],
		value = 'inline'
	)
	WEBCAM_START_BUTTON = gradio.Button(wording.get('start_button_label'))
	WEBCAM_STOP_BUTTON = gradio.Button(wording.get('stop_button_label'))


def listen() -> None:
	start_event = WEBCAM_START_BUTTON.click(start, inputs = WEBCAM_MODE_RADIO, outputs = WEBCAM_IMAGE)
	WEBCAM_MODE_RADIO.change(update, outputs = WEBCAM_IMAGE, cancels = start_event)
	WEBCAM_STOP_BUTTON.click(None, cancels = start_event)


def update() -> Update:
	return gradio.update(value = None)


def start(webcam_mode : WebcamMode) -> Generator[Frame, None, None]:
	if webcam_mode == 'inline':
		yield from start_inline()
	if webcam_mode == 'stream_udp':
		yield from start_stream('udp')
	if webcam_mode == 'stream_v4l2':
		yield from start_stream('v4l2')


def start_inline() -> Generator[Frame, None, None]:
	facefusion.globals.face_recognition = 'many'
	capture = cv2.VideoCapture(0)
	if capture.isOpened():
		while True:
			_, temp_frame = capture.read()
			temp_frame = process_stream_frame(temp_frame)
			if temp_frame is not None:
				yield normalize_frame_color(temp_frame)


def start_stream(mode : StreamMode) -> Generator[None, None, None]:
	facefusion.globals.face_recognition = 'many'
	capture = cv2.VideoCapture(0)
	ffmpeg_process = open_stream(mode)
	if capture.isOpened():
		while True:
			_, frame = capture.read()
			temp_frame = process_stream_frame(frame)
			if temp_frame is not None:
				ffmpeg_process.stdin.write(temp_frame.tobytes())
				yield normalize_frame_color(temp_frame)


def process_stream_frame(temp_frame : Frame) -> Frame:
	source_face = get_one_face(cv2.imread(facefusion.globals.source_path)) if facefusion.globals.source_path else None
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
		commands.extend([ '-b:v', '2000k', '-f', 'mpegts', 'udp://localhost:27000' ])
	if mode == 'v4l2':
		device_name = os.listdir('/sys/devices/virtual/video4linux')[0]
		commands.extend([ '-f', 'v4l2', '/dev/' + device_name ])
	return open_ffmpeg(commands)
