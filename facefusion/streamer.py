import os
import subprocess
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Deque, Generator

import cv2
import numpy
from tqdm import tqdm

from facefusion import ffmpeg_builder, logger, state_manager, wording
from facefusion.audio import create_empty_audio_frame
from facefusion.content_analyser import analyse_stream
from facefusion.ffmpeg import open_ffmpeg
from facefusion.filesystem import is_directory
from facefusion.processors.core import get_processors_modules
from facefusion.types import Fps, StreamMode, VisionFrame
from facefusion.vision import read_static_images


def multi_process_capture(camera_capture : cv2.VideoCapture, camera_fps : Fps) -> Generator[VisionFrame, None, None]:
	capture_deque : Deque[VisionFrame] = deque()

	with tqdm(desc = wording.get('streaming'), unit = 'frame', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		with ThreadPoolExecutor(max_workers = state_manager.get_item('execution_thread_count')) as executor:
			futures = []

			while camera_capture and camera_capture.isOpened():
				_, capture_frame = camera_capture.read()
				if analyse_stream(capture_frame, camera_fps):
					camera_capture.release()

				if numpy.any(capture_frame):
					future = executor.submit(process_stream_frame, capture_frame)
					futures.append(future)

				for future_done in [ future for future in futures if future.done() ]:
					capture_frame = future_done.result()
					capture_deque.append(capture_frame)
					futures.remove(future_done)

				while capture_deque:
					progress.update()
					yield capture_deque.popleft()


def process_stream_frame(target_vision_frame : VisionFrame) -> VisionFrame:
	source_vision_frames = read_static_images(state_manager.get_item('source_paths'))
	source_audio_frame = create_empty_audio_frame()
	source_voice_frame = create_empty_audio_frame()
	temp_vision_frame = target_vision_frame.copy()

	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		logger.disable()
		if processor_module.pre_process('stream'):
			logger.enable()
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
