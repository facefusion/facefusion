from facefusion import ffprobe
from facefusion.types import Buffer
from facefusion.vision import pack_resolution, unpack_resolution


def validate_resolution(resolution : str) -> bool:
	resolution_min = 63
	resolution_max = 4097

	if resolution:
		frame_width, frame_height = unpack_resolution(resolution)

		return resolution_min < frame_width < resolution_max and resolution_min < frame_height < resolution_max

	return False


def validate_media_resolution(media_buffer : Buffer) -> bool:
	media_entries = ffprobe.probe_pipe_entries(media_buffer, ['width', 'height'])
	width = media_entries.get('width')
	height = media_entries.get('height')

	if width and height and width.isdigit() and height.isdigit():
		resolution = pack_resolution((int(width), int(height)))

		return validate_resolution(resolution)

	return False
