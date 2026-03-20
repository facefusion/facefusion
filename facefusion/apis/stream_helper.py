import subprocess
import threading
from typing import Optional

import cv2

from facefusion import ffmpeg_builder
from facefusion.ffmpeg import open_ffmpeg
from facefusion.streamer import process_vision_frame
from facefusion.types import VisionFrame

STREAM_FPS : int = 30
STREAM_QUALITY : int = 80


def create_stream_encoder(width : int, height : int, stream_fps : int, stream_quality : int) -> subprocess.Popen[bytes]:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.capture_video(),
		ffmpeg_builder.set_media_resolution(str(width) + 'x' + str(height)),
		ffmpeg_builder.set_input_fps(stream_fps),
		ffmpeg_builder.set_input('-'),
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_quality('libx264', stream_quality),
		ffmpeg_builder.set_video_preset('libx264', 'ultrafast'),
		[ '-tune', 'zerolatency' ],
		[ '-maxrate', '4000k' ],
		[ '-bufsize', '8000k' ],
		[ '-g', str(stream_fps) ],
		[ '-f', 'mp4' ],
		[ '-movflags', 'frag_keyframe+empty_moov+default_base_moof+frag_every_frame' ],
		ffmpeg_builder.set_output('-')
	)
	return open_ffmpeg(commands)


def read_stream_output(process : subprocess.Popen[bytes], output_chunks : list, lock : threading.Lock) -> None:
	while True:
		chunk = process.stdout.read(4096)

		if not chunk:
			break

		with lock:
			output_chunks.append(chunk)


def encode_stream_frame(process : subprocess.Popen[bytes], vision_frame : VisionFrame, output_chunks : list, lock : threading.Lock) -> Optional[bytes]:
	raw_bytes = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB).tobytes()
	process.stdin.write(raw_bytes)
	process.stdin.flush()

	with lock:
		if output_chunks:
			encoded_bytes = b''.join(output_chunks)
			output_chunks.clear()
			return encoded_bytes

	return None


def close_stream_encoder(process : subprocess.Popen[bytes]) -> None:
	process.stdin.close()
	process.wait()


def process_stream_frame(vision_frame : VisionFrame) -> VisionFrame:
	return process_vision_frame(vision_frame)
