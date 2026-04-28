import asyncio
import os
import subprocess
from typing import Optional, Tuple, cast

from aiortc import MediaStreamTrack, QueuedVideoStreamTrack, RTCPeerConnection, RTCRtpSender
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame
from starlette.datastructures import Headers
from starlette.types import Scope

from facefusion.common_helper import is_linux, is_macos
from facefusion.streamer import process_vision_frame
from facefusion.types import FrameStream, Resolution, WebSocketStreamMode


def process_stream_frame(target_stream_frame : VideoFrame) -> VideoFrame:
	target_vision_frame = target_stream_frame.to_ndarray(format = 'bgr24')
	output_vision_frame = process_vision_frame(target_vision_frame)
	output_stream_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
	output_stream_frame.pts = target_stream_frame.pts
	output_stream_frame.time_base = target_stream_frame.time_base
	return output_stream_frame


def create_output_track(rtc_connection : RTCPeerConnection, buffer_size : int) -> Tuple[QueuedVideoStreamTrack, RTCRtpSender]:
	output_track = QueuedVideoStreamTrack(buffer_size = buffer_size)
	sender = rtc_connection.addTrack(output_track)
	return output_track, sender


async def process_and_enqueue(target_track : MediaStreamTrack, output_track : QueuedVideoStreamTrack) -> None:
	loop = asyncio.get_running_loop()

	while True:
		try:
			target_stream_frame = await target_track.recv()
		except MediaStreamError:
			pass

		output_stream_frame = await loop.run_in_executor(None, process_stream_frame, target_stream_frame) #type:ignore[arg-type]
		await output_track.put(output_stream_frame)


def on_video_track(rtc_connection : RTCPeerConnection, output_track : QueuedVideoStreamTrack, target_track : MediaStreamTrack) -> None:
	if target_track.kind == 'audio':
		rtc_connection.addTrack(target_track)

	if target_track.kind == 'video':
		asyncio.create_task(process_and_enqueue(target_track, output_track))


def calculate_bitrate(resolution : Resolution) -> int:
	pixel_total = resolution[0] * resolution[1]
	bitrate_factor = 5000 / (1920 * 1080)
	return max(400, round(pixel_total * bitrate_factor))


def calculate_buffer_size(resolution : Resolution) -> int:
	return calculate_bitrate(resolution) * 2


def get_stream_mode(scope : Scope) -> Optional[WebSocketStreamMode]:
	protocol_header = Headers(scope = scope).get('Sec-WebSocket-Protocol')

	if protocol_header:
		for protocol in protocol_header.split(','):
			protocol = protocol.strip()

			if protocol in [ 'image', 'video' ]:
				return cast(WebSocketStreamMode, protocol)

	return None


def read_pipe_buffer(pipe_handle : int, size : int) -> Optional[bytes]:
	byte_buffer = bytearray()
	frame_data = os.read(pipe_handle, size - len(byte_buffer))

	while frame_data:
		byte_buffer += frame_data

		if len(byte_buffer) == size:
			return bytes(byte_buffer)

		frame_data = os.read(pipe_handle, size - len(byte_buffer))

	return None


def stream_frames(process : subprocess.Popen[bytes]) -> FrameStream:
	pipe_handle = process.stdout.fileno()

	if is_linux() or is_macos():
		os.set_blocking(pipe_handle, True)

	header = read_pipe_buffer(pipe_handle, 32)

	if header:
		frame_header = read_pipe_buffer(pipe_handle, 12)

		while frame_header:
			frame_size = int.from_bytes(frame_header[0:4], 'little')
			frame_data = read_pipe_buffer(pipe_handle, frame_size)

			if frame_data:
				yield frame_data

			frame_header = read_pipe_buffer(pipe_handle, 12)
