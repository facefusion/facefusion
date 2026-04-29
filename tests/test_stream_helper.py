import os
import subprocess

from facefusion import ffmpeg_builder
from facefusion.apis.stream_helper import calculate_bitrate, calculate_buffer_size, forward_stream_frame, get_websocket_stream_mode, read_pipe_buffer
from facefusion.vision import pack_resolution


def make_scope(protocol : str) -> dict[str, object]:
	return\
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', protocol.encode()) ]
	}


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


def test_get_stream_mode() -> None:
	assert get_websocket_stream_mode(make_scope('image')) == 'image'
	assert get_websocket_stream_mode(make_scope('video')) == 'video'


def test_read_pipe_buffer() -> None:
	read_fd, write_fd = os.pipe()
	os.write(write_fd, b'abcdefgh')
	os.close(write_fd)

	assert read_pipe_buffer(read_fd, 4) == b'abcd'
	assert read_pipe_buffer(read_fd, 4) == b'efgh'
	assert read_pipe_buffer(read_fd, 1) is None

	os.close(read_fd)


def test_forward_frames() -> None:
	resolution = (320, 240)
	frame_size = resolution[0] * resolution[1] * 3
	commands = ffmpeg_builder.run(ffmpeg_builder.chain(
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(pack_resolution(resolution)),
		ffmpeg_builder.set_input_fps(30),
		ffmpeg_builder.set_input('-'),
		ffmpeg_builder.set_video_encoder('libvpx'),
		ffmpeg_builder.set_encoder_deadline('realtime'),
		ffmpeg_builder.set_stream_quality(400),
		ffmpeg_builder.set_muxer('ivf'),
		ffmpeg_builder.set_output('-')
	))
	encoder = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	encoder.stdin.write(bytes(frame_size))
	encoder.stdin.close()

	for stream_buffer in forward_stream_frame(encoder):
		assert 0 < len(stream_buffer) < frame_size
