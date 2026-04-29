import math
import os
import subprocess
from typing import Iterator, Optional, cast

from starlette.datastructures import Headers
from starlette.types import Scope

from facefusion.common_helper import is_linux, is_macos
from facefusion.types import Resolution, StreamBuffer, WebSocketStreamMode


def calculate_bitrate(resolution : Resolution) -> int: # TODO : improve the bitrate calculation
	pixel_total = resolution[0] * resolution[1]
	bitrate_factor = 3500 / math.sqrt(1920 * 1080)
	return max(400, round(math.sqrt(pixel_total) * bitrate_factor))


def calculate_buffer_size(resolution : Resolution) -> int:
	return calculate_bitrate(resolution) * 2


def get_websocket_stream_mode(scope : Scope) -> Optional[WebSocketStreamMode]:
	protocol_header = Headers(scope = scope).get('Sec-WebSocket-Protocol')

	if protocol_header:
		for protocol in protocol_header.split(','):
			websocket_stream_mode = protocol.strip()

			if websocket_stream_mode in [ 'image', 'video' ]:
				return cast(WebSocketStreamMode, websocket_stream_mode)

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


def forward_stream_frame(process : subprocess.Popen[bytes]) -> Iterator[StreamBuffer]:
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


def is_jpeg_buffer(frame_buffer : bytes) -> bool:
	return len(frame_buffer) > 3 and frame_buffer[:3] == b'\xff\xd8\xff'
