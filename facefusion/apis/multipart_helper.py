import secrets
from typing import Iterator, List

from starlette.responses import StreamingResponse

from facefusion.types import Buffer, VisionFrame
from facefusion.vision import to_buffer


def create_multipart_response(vision_frames : List[VisionFrame]) -> StreamingResponse:
	boundary = secrets.token_hex(16)
	content = stream_multipart(vision_frames, boundary)
	media_type = 'multipart/mixed; boundary=' + boundary

	return StreamingResponse(content, media_type = media_type)


def stream_multipart(vision_frames : List[VisionFrame], boundary : str) -> Iterator[Buffer]:
	eol = '\r\n'

	for vision_frame in vision_frames:
		vision_buffer = to_buffer(vision_frame)
		content_total = len(vision_buffer)

		part_header = '--' + boundary + eol
		part_header += 'Content-Type: image/jpeg' + eol
		part_header += 'Content-Length: ' + str(content_total) + eol + eol

		yield part_header.encode() + vision_buffer + eol.encode()

	yield ('--' + boundary + '--' + eol).encode()
