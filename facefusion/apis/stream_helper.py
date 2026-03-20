import os
import subprocess
import tempfile
from typing import Tuple

import cv2

from facefusion import ffmpeg_builder, mediamtx
from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame

STREAM_FPS : int = 30
STREAM_QUALITY : int = 45
STREAM_AUDIO_RATE : int = 48000
DTLS_CERT_FILE : str = os.path.join(tempfile.gettempdir(), 'facefusion_dtls_cert.pem')
DTLS_KEY_FILE : str = os.path.join(tempfile.gettempdir(), 'facefusion_dtls_key.pem')


def create_dtls_certificate() -> None:
	if os.path.isfile(DTLS_CERT_FILE) and os.path.isfile(DTLS_KEY_FILE):
		return

	subprocess.run([
		'openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:prime256v1',
		'-keyout', DTLS_KEY_FILE, '-out', DTLS_CERT_FILE,
		'-days', '365', '-nodes', '-subj', '/CN=facefusion'
	], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)


def create_whip_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> Tuple[subprocess.Popen[bytes], int]:
	create_dtls_certificate()
	audio_read_fd, audio_write_fd = os.pipe()
	whip_url = mediamtx.get_whip_url()
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
		[ '-maxrate', '1500k' ],
		[ '-bufsize', '3000k' ],
		[ '-g', str(stream_fps) ],
		[ '-c:a', 'libopus' ],
		[ '-f', 'whip' ],
		[ '-cert_file', DTLS_CERT_FILE ],
		[ '-key_file', DTLS_KEY_FILE ],
		ffmpeg_builder.set_output(whip_url)
	)
	commands = ffmpeg_builder.run(commands)
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


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)
