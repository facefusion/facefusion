from typing import Optional
import cv2
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.typing import Frame
from facefusion.face_analyser import get_one_face
from facefusion.processors.frame.core import load_frame_processor_module
from facefusion.utilities import open_ffmpeg

WEBCAM_START_BUTTON : Optional[gradio.Button] = None
WEBCAM_STOP_BUTTON : Optional[gradio.Button] = None
STATE : Optional[str] = None


def render() -> None:
	global WEBCAM_START_BUTTON
	global WEBCAM_STOP_BUTTON

	WEBCAM_START_BUTTON = gradio.Button(wording.get('start_button_label'))
	WEBCAM_STOP_BUTTON = gradio.Button(wording.get('stop_button_label'))


def listen() -> None:
	WEBCAM_START_BUTTON.click(start)
	WEBCAM_STOP_BUTTON.click(stop)


def start() -> None:
	global STATE

	STATE = 'start'
	capture = cv2.VideoCapture(0)
	capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
	capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
	capture.set(cv2.CAP_PROP_FPS, 30)
	while STATE == 'start':
		_, frame = capture.read()
		temp_frame = process_stream_frame(frame)
		if temp_frame is not None:
			cv2.imshow('FaceFusionCam', temp_frame)
		cv2.waitKey(1)
	capture.release()
	cv2.destroyAllWindows()


def __start() -> None:
	global STATE

	STATE = 'start'
	capture = cv2.VideoCapture(0)
	commands =\
	[
		'-f', 'rawvideo',
		'-pix_fmt', 'bgr24',
		'-s', '640x480',
		'-r', '30',
		'-i', '-',
		'-preset', 'fast',
		'-b:v', '2000k',
		'-f', 'mpegts',
		'udp://localhost:8080'
	]
	ffmpeg_process = open_ffmpeg(commands)
	while STATE == 'start':
		_, frame = capture.read()
		temp_frame = process_stream_frame(frame)
		if temp_frame.any():
			ffmpeg_process.stdin.write(temp_frame.tobytes())

	capture.release()
	cv2.destroyAllWindows()
	ffmpeg_process.stdin.close()
	ffmpeg_process.wait()


def stop() -> None:
	global STATE

	STATE = 'stop'


def process_stream_frame(temp_frame : Frame) -> Frame:
	facefusion.globals.face_recognition = 'many'
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
