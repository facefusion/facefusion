import subprocess

import cv2

from facefusion import ffmpeg_builder
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


def create_vp8_pipe_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		[ '-c:v', 'libvpx' ],
		[ '-deadline', 'realtime' ],
		[ '-cpu-used', '8' ],
		[ '-pix_fmt', 'yuv420p' ],
		[ '-crf', '10' ],
		[ '-b:v', compute_bitrate(width, height) ],
		[ '-maxrate', compute_bitrate(width, height) ],
		[ '-bufsize', compute_bufsize(width, height) ],
		[ '-g', str(stream_fps) ],
		[ '-keyint_min', str(stream_fps) ],
		[ '-error-resilient', '1' ],
		[ '-lag-in-frames', '0' ],
		[ '-rc_lookahead', '0' ],
		[ '-threads', '4' ],
		[ '-an' ],
		[ '-f', 'ivf' ],
		ffmpeg_builder.set_output('-')
	)
	commands = ffmpeg_builder.run(commands)
	process = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	return process


def feed_whip_frame(process : subprocess.Popen[bytes], vision_frame : VisionFrame) -> None:
	raw_bytes = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB).tobytes()
	process.stdin.write(raw_bytes)
	process.stdin.flush()


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)
