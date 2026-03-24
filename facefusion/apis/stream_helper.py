import os
import subprocess
import tempfile
import threading
from typing import List, Optional, Tuple

import cv2

from facefusion import ffmpeg_builder
from facefusion.common_helper import is_windows
from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame

STREAM_FPS : int = 30
STREAM_QUALITY : int = 80
STREAM_AUDIO_RATE : int = 48000
DTLS_CERT_FILE : str = os.path.join(tempfile.gettempdir(), 'facefusion_dtls_cert.pem')
DTLS_KEY_FILE : str = os.path.join(tempfile.gettempdir(), 'facefusion_dtls_key.pem')


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


def create_dtls_certificate() -> None:
	if os.path.isfile(DTLS_CERT_FILE) and os.path.isfile(DTLS_KEY_FILE):
		return

	subprocess.run([
		'openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:prime256v1',
		'-keyout', DTLS_KEY_FILE, '-out', DTLS_CERT_FILE,
		'-days', '365', '-nodes', '-subj', '/CN=facefusion'
	], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)


def create_whip_encoder(width : int, height : int, stream_fps : int, stream_quality : int, whip_url : str) -> Tuple[subprocess.Popen[bytes], int]:
	create_dtls_certificate()
	audio_read_fd, audio_write_fd = os.pipe()
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		[ '-use_wallclock_as_timestamps', '1' ],
		[ '-f', 's16le', '-ar', str(STREAM_AUDIO_RATE), '-ac', '2', '-i', 'pipe:' + str(audio_read_fd) ],
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_quality('libx264', stream_quality),
		ffmpeg_builder.set_video_preset('libx264', 'ultrafast'),
		[ '-pix_fmt', 'yuv420p' ],
		[ '-profile:v', 'baseline' ],
		[ '-tune', 'zerolatency' ],
		[ '-maxrate', compute_bitrate(width, height) ],
		[ '-bufsize', compute_bufsize(width, height) ],
		[ '-g', str(stream_fps) ],
		[ '-c:a', 'libopus' ],
		[ '-f', 'whip' ],
		[ '-cert_file', DTLS_CERT_FILE ],
		[ '-key_file', DTLS_KEY_FILE ],
		ffmpeg_builder.set_output(whip_url)
	)
	commands = ffmpeg_builder.run(commands)

	if is_windows():
		os.set_inheritable(audio_read_fd, True)
		process = subprocess.Popen(commands, stdin = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = False)
	else:
		process = subprocess.Popen(commands, stdin = subprocess.PIPE, stderr = subprocess.PIPE, pass_fds = (audio_read_fd,))

	os.close(audio_read_fd)
	return process, audio_write_fd


def feed_whip_frame(process : subprocess.Popen[bytes], vision_frame : VisionFrame) -> None:
	raw_bytes = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB).tobytes()
	process.stdin.write(raw_bytes)
	process.stdin.flush()


def feed_whip_audio(audio_write_fd : int, audio_data : bytes) -> None:
	os.write(audio_write_fd, audio_data)


def close_whip_encoder(process : subprocess.Popen[bytes], audio_write_fd : int) -> None:
	os.close(audio_write_fd)
	process.stdin.close()
	process.terminate()
	process.wait(timeout = 5)


def create_fmp4_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> Tuple[subprocess.Popen[bytes], int]:
	audio_read_fd, audio_write_fd = os.pipe()
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		[ '-use_wallclock_as_timestamps', '1' ],
		[ '-f', 's16le', '-ar', str(STREAM_AUDIO_RATE), '-ac', '2', '-i', 'pipe:' + str(audio_read_fd) ],
		[ '-thread_queue_size', '512' ],
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_quality('libx264', stream_quality),
		ffmpeg_builder.set_video_preset('libx264', 'ultrafast'),
		[ '-pix_fmt', 'yuv420p' ],
		[ '-profile:v', 'baseline' ],
		[ '-tune', 'zerolatency' ],
		[ '-maxrate', compute_bitrate(width, height) ],
		[ '-bufsize', compute_bufsize(width, height) ],
		[ '-g', str(stream_fps) ],
		[ '-c:a', 'aac' ],
		[ '-b:a', '128k' ],
		[ '-f', 'mp4' ],
		[ '-movflags', 'frag_keyframe+empty_moov+default_base_moof+frag_every_frame' ],
		ffmpeg_builder.set_output('-')
	)
	commands = ffmpeg_builder.run(commands)

	if is_windows():
		os.set_inheritable(audio_read_fd, True)
		process = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, close_fds = False)
	else:
		process = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, pass_fds = (audio_read_fd,))

	os.close(audio_read_fd)
	return process, audio_write_fd


def read_fmp4_output(process : subprocess.Popen[bytes], output_chunks : List[bytes], lock : threading.Lock) -> None:
	while True:
		chunk = process.stdout.read(4096)

		if not chunk:
			break

		with lock:
			output_chunks.append(chunk)


def collect_fmp4_chunks(output_chunks : List[bytes], lock : threading.Lock) -> Optional[bytes]:
	with lock:
		if output_chunks:
			encoded_bytes = b''.join(output_chunks)
			output_chunks.clear()
			return encoded_bytes

	return None


def close_fmp4_encoder(process : subprocess.Popen[bytes], audio_write_fd : int) -> None:
	if audio_write_fd > 0:
		os.close(audio_write_fd)
	process.stdin.close()
	process.terminate()
	process.wait(timeout = 5)


def create_rtp_encoder(width : int, height : int, stream_fps : int, stream_quality : int, rtp_port : int) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_quality('libx264', stream_quality),
		ffmpeg_builder.set_video_preset('libx264', 'ultrafast'),
		[ '-pix_fmt', 'yuv420p' ],
		[ '-profile:v', 'baseline' ],
		[ '-tune', 'zerolatency' ],
		[ '-maxrate', compute_bitrate(width, height) ],
		[ '-bufsize', compute_bufsize(width, height) ],
		[ '-g', str(stream_fps) ],
		[ '-an' ],
		[ '-f', 'rtp' ],
		[ '-payload_type', '96' ],
		ffmpeg_builder.set_output('rtp://127.0.0.1:' + str(rtp_port) + '?pkt_size=1200')
	)
	commands = ffmpeg_builder.run(commands)
	process = subprocess.Popen(commands, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
	return process


def create_h264_pipe_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_quality('libx264', stream_quality),
		ffmpeg_builder.set_video_preset('libx264', 'ultrafast'),
		[ '-pix_fmt', 'yuv420p' ],
		[ '-profile:v', 'baseline' ],
		[ '-tune', 'zerolatency' ],
		[ '-maxrate', compute_bitrate(width, height) ],
		[ '-bufsize', compute_bufsize(width, height) ],
		[ '-g', '1' ],
		[ '-an' ],
		[ '-f', 'h264' ],
		ffmpeg_builder.set_output('-')
	)
	commands = ffmpeg_builder.run(commands)
	process = subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	return process


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


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)
