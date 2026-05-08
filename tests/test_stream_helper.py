import os

from facefusion.apis.stream_helper import calculate_bitrate, calculate_buffer_size, detect_websocket_stream_mode, read_pipe_buffer


def test_calculate_bitrate() -> None:
	assert calculate_bitrate((320, 240)) == 674
	assert calculate_bitrate((640, 480)) == 1347
	assert calculate_bitrate((1280, 720)) == 2333
	assert calculate_bitrate((1920, 1080)) == 3500
	assert calculate_bitrate((3840, 2160)) == 7000


def test_calculate_buffer_size() -> None:
	assert calculate_buffer_size((320, 240)) == 1348
	assert calculate_buffer_size((640, 480)) == 2694
	assert calculate_buffer_size((1280, 720)) == 4666
	assert calculate_buffer_size((1920, 1080)) == 7000
	assert calculate_buffer_size((3840, 2160)) == 14000


def test_detect_websocket_stream_mode() -> None:
	scope =\
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'image') ]
	}

	assert detect_websocket_stream_mode(scope) == 'image'

	scope =\
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'video') ]
	}

	assert detect_websocket_stream_mode(scope) == 'video'


def test_read_pipe_buffer() -> None:
	read_pipe, write_pipe = os.pipe()
	os.write(write_pipe, b'123456')
	os.close(write_pipe)

	assert read_pipe_buffer(read_pipe, 4) == b'123'
	assert read_pipe_buffer(read_pipe, 4) == b'456'
	assert read_pipe_buffer(read_pipe, 1) is None

	os.close(read_pipe)
