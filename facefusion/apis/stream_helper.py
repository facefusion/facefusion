import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

import cv2
import requests

from facefusion import ffmpeg_builder
from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame

STREAM_FPS : int = 30
STREAM_QUALITY : int = 45
MEDIAMTX_WHIP_PORT : int = 8889
MEDIAMTX_PATH : str = 'stream'
MEDIAMTX_CONFIG : str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mediamtx.yml')
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


def create_whip_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> subprocess.Popen[bytes]:
	create_dtls_certificate()
	whip_url = 'http://localhost:' + str(MEDIAMTX_WHIP_PORT) + '/' + MEDIAMTX_PATH + '/whip'
	commands = ffmpeg_builder.chain(
		[ '-use_wallclock_as_timestamps', '1' ],
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input('-'),
		[ '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo' ],
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
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stderr = subprocess.PIPE)


def start_mediamtx() -> Optional[subprocess.Popen[bytes]]:
	stop_stale_mediamtx()
	mediamtx_path = shutil.which('mediamtx')

	if not mediamtx_path:
		mediamtx_path = '/home/henry/local/bin/mediamtx'

	return subprocess.Popen(
		[ mediamtx_path, MEDIAMTX_CONFIG ],
		stdout = subprocess.DEVNULL,
		stderr = subprocess.DEVNULL
	)


def stop_stale_mediamtx() -> None:
	subprocess.run([ 'fuser', '-k', str(MEDIAMTX_WHIP_PORT) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	subprocess.run([ 'fuser', '-k', '8189/udp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	subprocess.run([ 'fuser', '-k', '9997/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	time.sleep(1)


def wait_for_mediamtx() -> bool:
	for _ in range(10):
		try:
			response = requests.get('http://localhost:9997/v3/paths/list', timeout = 1)

			if response.status_code == 200:
				return True
		except Exception:
			pass
		time.sleep(0.5)
	return False


def stop_mediamtx(process : subprocess.Popen[bytes]) -> None:
	process.terminate()
	process.wait()


def feed_whip_frame(process : subprocess.Popen[bytes], vision_frame : VisionFrame) -> None:
	raw_bytes = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB).tobytes()
	process.stdin.write(raw_bytes)
	process.stdin.flush()


def close_whip_encoder(process : subprocess.Popen[bytes]) -> None:
	process.stdin.close()
	process.terminate()
	process.wait(timeout = 5)


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)
