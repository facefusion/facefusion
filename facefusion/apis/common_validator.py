from facefusion import ffprobe
from facefusion.types import Buffer
from facefusion.vision import unpack_resolution


def validate_resolution(resolution : str) -> bool:
	resolution_min = 63
	resolution_max = 4097

	if resolution:
		frame_width, frame_height = unpack_resolution(resolution)

		return resolution_min < frame_width < resolution_max and resolution_min < frame_height < resolution_max

	return False


def validate_image_resolution(image_buffer : Buffer) -> bool:
	image_entries = ffprobe.probe_buffer_entries(image_buffer, [ 'width', 'height' ])
	width = image_entries.get('width')
	height = image_entries.get('height')

	if width and height and width.isdigit() and height.isdigit():
		return validate_resolution(width + 'x' + height)

	return False
