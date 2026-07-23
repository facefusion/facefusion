import subprocess
from typing import Optional, Tuple

import numpy

from facefusion import ffmpeg, ffprobe
from facefusion.types import Fps, Resolution, VideoPoolSet, VideoReader, VisionFrame, VisionFrameSet

VIDEO_POOL_SET : VideoPoolSet =\
{
	'reader': {},
	'writer': {}
}


def get_reader(video_path : str) -> VideoReader:
	if video_path not in VIDEO_POOL_SET.get('reader'):
		video_metadata = ffprobe.extract_static_video_metadata(video_path)

		VIDEO_POOL_SET['reader'][video_path] =\
		{
			'process': ffmpeg.open_video_reader(video_path, 0, video_metadata.get('fps')),
			'video_path': video_path,
			'video_metadata': video_metadata,
			'position': 0,
			'frame_set': {}
		}

	return VIDEO_POOL_SET.get('reader').get(video_path)


def conditional_set_video_reader_position(video_reader : VideoReader, frame_position : int) -> None:
	skip_margin = 128
	skipping = video_reader.get('position') < frame_position and frame_position - video_reader.get('position') <= skip_margin

	while skipping:
		has_vision_frame, vision_frame = read_video_reader_frame(video_reader)
		skipping = has_vision_frame and video_reader.get('position') < frame_position

	if not video_reader.get('position') == frame_position:
		restart_video_reader(video_reader, frame_position)


def restart_video_reader(video_reader : VideoReader, frame_position : int) -> None:
	video_reader.get('process').kill()
	video_reader.get('process').wait()
	video_reader['process'] = ffmpeg.open_video_reader(video_reader.get('video_path'), frame_position, video_reader.get('video_metadata').get('fps'))
	video_reader['position'] = frame_position
	video_reader['frame_set'].clear()


def read_video_reader_frame(video_reader : VideoReader) -> Tuple[bool, Optional[VisionFrame]]:
	width, height = video_reader.get('video_metadata').get('resolution')
	frame_size = width * height * 3
	frame_buffer = video_reader.get('process').stdout.read(frame_size)

	if len(frame_buffer) == frame_size:
		video_reader['position'] = video_reader.get('position') + 1
		return True, numpy.frombuffer(frame_buffer, numpy.uint8).reshape(height, width, 3)
	return False, None


def read_video_reader_window(video_reader : VideoReader, frame_start : int, frame_end : int) -> VisionFrameSet:
	frame_set = video_reader.get('frame_set')
	buffer_margin = 16
	read_start = max(frame_start, 0)
	read_end = frame_end

	if video_reader.get('video_metadata').get('frame_total') > 0:
		read_end = min(read_end, video_reader.get('video_metadata').get('frame_total') - 1)

	if read_start not in frame_set and (read_start < video_reader.get('position') or read_start > video_reader.get('position') + buffer_margin):
		restart_video_reader(video_reader, read_start)

	reading = video_reader.get('position') <= read_end

	while reading:
		has_vision_frame, vision_frame = read_video_reader_frame(video_reader)

		if has_vision_frame:
			frame_set[video_reader.get('position') - 1] = vision_frame
		reading = has_vision_frame and video_reader.get('position') <= read_end

	evict_video_reader_frame_set(video_reader, read_start, buffer_margin)
	return frame_set


def evict_video_reader_frame_set(video_reader : VideoReader, frame_start : int, buffer_margin : int) -> None:
	frame_set = video_reader.get('frame_set')
	eviction_numbers = [ frame_number for frame_number in frame_set if frame_number < frame_start - buffer_margin ]

	for frame_number in eviction_numbers:
		del frame_set[frame_number]


def get_writer(target_path : str, temp_video_fps : Fps, temp_video_resolution : Resolution, output_video_resolution : Resolution, output_video_fps : Fps) -> subprocess.Popen[bytes]:
	if target_path not in VIDEO_POOL_SET.get('writer'):
		VIDEO_POOL_SET['writer'][target_path] = ffmpeg.open_video_writer(target_path, temp_video_fps, temp_video_resolution, output_video_resolution, output_video_fps)

	return VIDEO_POOL_SET.get('writer').get(target_path)


def write_video_writer_frame(video_writer : subprocess.Popen[bytes], vision_frame : VisionFrame) -> None:
	video_writer.stdin.write(vision_frame.tobytes())


def close_video_writer(video_writer : subprocess.Popen[bytes]) -> bool:
	video_writer.stdin.close()
	video_writer.wait()
	return video_writer.returncode == 0


def clear_video_pool() -> None:
	for video_reader in VIDEO_POOL_SET.get('reader').values():
		video_reader.get('process').kill()
		video_reader.get('process').wait()

	for video_writer in VIDEO_POOL_SET.get('writer').values():
		video_writer.kill()
		video_writer.wait()

	VIDEO_POOL_SET['reader'].clear()
	VIDEO_POOL_SET['writer'].clear()
