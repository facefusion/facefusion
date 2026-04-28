import os
import subprocess

from facefusion.apis.stream_helper import calculate_bitrate, calculate_buffer_size, get_stream_mode, read_pipe_buffer, stream_frames


def make_scope(protocol : str) -> dict[str, object]:
	return\
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', protocol.encode()) ]
	}


def test_calculate_bitrate() -> None:
	assert calculate_bitrate((320, 240)) == 400
	assert calculate_bitrate((640, 480)) == 741
	assert calculate_bitrate((1280, 720)) == 2222
	assert calculate_bitrate((1920, 1080)) == 5000
	assert calculate_bitrate((3840, 2160)) == 20000


def test_calculate_buffer_size() -> None:
	assert calculate_buffer_size((320, 240)) == 800
	assert calculate_buffer_size((640, 480)) == 1482
	assert calculate_buffer_size((1280, 720)) == 4444
	assert calculate_buffer_size((1920, 1080)) == 10000
	assert calculate_buffer_size((3840, 2160)) == 40000


def test_get_stream_mode() -> None:
	assert get_stream_mode(make_scope('image')) == 'image'
	assert get_stream_mode(make_scope('video')) == 'video'


def test_read_pipe_buffer() -> None:
	read_fd, write_fd = os.pipe()
	os.write(write_fd, b'abcdefgh')
	os.close(write_fd)

	assert read_pipe_buffer(read_fd, 4) == b'abcd'
	assert read_pipe_buffer(read_fd, 4) == b'efgh'
	assert read_pipe_buffer(read_fd, 1) is None

	os.close(read_fd)


def test_stream_frames() -> None:
	encoder = subprocess.Popen(
	[
		'ffmpeg',
		'-loglevel', 'error',
		'-f', 'rawvideo',
		'-pix_fmt', 'rgb24',
		'-s', '320x240',
		'-r', '30',
		'-i', '-',
		'-c:v', 'libvpx',
		'-deadline', 'realtime',
		'-b:v', '400k',
		'-an', '-f',
		'ivf', '-'
	], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

	frame_size = 320 * 240 * 3
	encoder.stdin.write(bytes(frame_size))
	encoder.stdin.close()

	frames_received = list(stream_frames(encoder))

	assert len(frames_received) > 0
	assert all(isinstance(frame, bytes) for frame in frames_received)
