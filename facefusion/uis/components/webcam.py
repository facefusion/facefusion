from typing import Optional, Generator
import cv2
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.typing import Frame
from facefusion.face_analyser import get_one_face
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.uis.core import normalize_frame

WEBCAM_IMAGE : Optional[gradio.Image] = None
WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global WEBCAM_IMAGE
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_IMAGE = gradio.Image(
		label = wording.get('webcam_image_label'),
		source = 'canvas'
	)
	WEBCAM_START_BUTTON = gradio.Button(wording.get('start_button_label'))
	WEBCAM_STOP_BUTTON = gradio.Button(wording.get('stop_button_label'))


def listen() -> None:
	start_event = WEBCAM_START_BUTTON.click(start, outputs = WEBCAM_IMAGE)
	WEBCAM_STOP_BUTTON.click(None, cancels = start_event)


def start() -> Generator[Frame, None, None]:
	facefusion.globals.face_recognition = 'many'
	capture = cv2.VideoCapture(0)
	while True:
		_, temp_frame = capture.read()
		temp_frame = normalize_frame(temp_frame)
		temp_frame = process_stream_frame(temp_frame)
		if temp_frame is not None:
			yield temp_frame


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
