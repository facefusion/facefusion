import os
import struct
import subprocess
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import List

import cv2

from facefusion import rtc, state_manager
from facefusion.common_helper import is_linux, is_macos
from facefusion.streamer import process_vision_frame
from facefusion.types import BitRate, Resolution, RtcPeer, VisionFrame


def calculate_stream_bitrate(resolution : Resolution) -> BitRate:
	pixel_total = resolution[0] * resolution[1]

	if pixel_total > 3840 * 2160:
		return 15000
	if pixel_total > 2560 * 1440:
		return 10000
	if pixel_total > 1920 * 1080:
		return 6000
	if pixel_total > 1280 * 720:
		return 3500
	if pixel_total > 640 * 480:
		return 2000
	if pixel_total > 320 * 240:
		return 1000
	return 400


def read_pipe_bytes(pipe_fd : int, size : int) -> bytes:
	data = b''

	while len(data) < size:
		chunk = os.read(pipe_fd, size - len(data))

		if not chunk:
			return b''

		data += chunk

	return data


def forward_stream_frames(peers : List[RtcPeer], encoder : subprocess.Popen[bytes]) -> None:
	output_pipe = encoder.stdout.fileno()

	if is_linux() or is_macos():
		os.set_blocking(output_pipe, True)

	read_pipe_bytes(output_pipe, 32)

	while frame_header := read_pipe_bytes(output_pipe, 12):
		frame_size = struct.unpack('<I', frame_header[:4])[0]
		frame_bytes = read_pipe_bytes(output_pipe, frame_size)

		if frame_bytes:
			rtc.send_to_peers(peers, frame_bytes)


def process_stream_frame(target_vision_frame : VisionFrame) -> bytes:
	output_vision_frame = process_vision_frame(target_vision_frame)
	output_vision_frame = output_vision_frame[:, :, ::-1]
	return output_vision_frame.tobytes()


def run_video_pipeline(peers : List[RtcPeer], stream_pipe : subprocess.Popen[bytes], target_path : str, video_fps : float) -> None:
	execution_thread_count = state_manager.get_item('execution_thread_count')
	frame_interval = 1.0 / video_fps
	video_capture = cv2.VideoCapture(target_path)

	with ThreadPoolExecutor(max_workers = execution_thread_count) as executor:
		while rtc.is_peer_connected(peers):
			video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
			frame_futures : List[Future[bytes]] = []
			next_frame_time = time.monotonic()

			try:
				while rtc.is_peer_connected(peers) and video_capture.isOpened():
					if frame_futures and len(frame_futures) >= execution_thread_count * 2:
						stream_pipe.stdin.write(frame_futures.pop(0).result())

					while frame_futures and frame_futures[0].done():
						stream_pipe.stdin.write(frame_futures.pop(0).result())

					success, vision_frame = video_capture.read()

					if not success:
						break

					frame_futures.append(executor.submit(process_stream_frame, vision_frame))
					next_frame_time += frame_interval
					sleep_time = next_frame_time - time.monotonic()

					if sleep_time > 0:
						time.sleep(sleep_time)
			finally:
				while frame_futures and rtc.is_peer_connected(peers):
					stream_pipe.stdin.write(frame_futures.pop(0).result())

				frame_futures.clear()

	video_capture.release()
	stream_pipe.stdin.close()
	stream_pipe.wait()
