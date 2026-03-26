from typing import Optional

from starlette.datastructures import Headers
from starlette.types import Scope

from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame

STREAM_FPS : int = 30
STREAM_QUALITY : int = 80


def compute_bitrate(width : int, height : int) -> str:
	pixels = width * height

	if pixels <= 320 * 240:
		return '400k'
	if pixels <= 640 * 480:
		return '1000k'
	if pixels <= 1280 * 720:
		return '2000k'
	if pixels <= 1920 * 1080:
		return '3500k'
	return '5000k'


def compute_bufsize(width : int, height : int) -> str:
	pixels = width * height

	if pixels <= 320 * 240:
		return '800k'
	if pixels <= 640 * 480:
		return '2000k'
	if pixels <= 1280 * 720:
		return '4000k'
	if pixels <= 1920 * 1080:
		return '7000k'
	return '10000k'


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)


def get_stream_mode(scope : Scope) -> Optional[str]:
	protocol_header = Headers(scope = scope).get('Sec-WebSocket-Protocol')

	if protocol_header:
		for protocol in protocol_header.split(','):
			protocol = protocol.strip()

			if protocol in [ 'image', 'video' ]:
				return protocol

	return None
