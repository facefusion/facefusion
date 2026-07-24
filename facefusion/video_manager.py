from typing import Optional

import numpy

from facefusion import ffmpeg, ffprobe, frame_store
from facefusion.types import Fps, Resolution, VideoMetadata, VideoPoolSet, VideoReader, VideoWriter, VisionFrame, VisionFrameSet

VIDEO_POOL_SET : VideoPoolSet =\
{
	'reader': {},
	'writer': {}
}


#todo: needs review - [lifecycle] [critical: medium] pooled reader per path is created without lock and only reaped via clear_video_pool
def get_reader(video_path : str) -> VideoReader:
	if video_path not in VIDEO_POOL_SET.get('reader'):
		video_metadata = ffprobe.extract_static_video_metadata(video_path)

		VIDEO_POOL_SET['reader'][video_path] =\
		{
			'process': ffmpeg.create_video_reader(video_path, 0, video_metadata),
			'file_path': video_path,
			'metadata': video_metadata,
			'position': 0
		}

	return VIDEO_POOL_SET.get('reader').get(video_path)


#todo: needs review - [seeking] [critical: high] forward skip up to 128 frames by draining the pipe, everything else refreshes the process
def conditional_set_video_reader_position(video_reader : VideoReader, frame_position : int) -> None:
	skip_margin = 128
	skip_total = frame_position - video_reader.get('position')

	if skip_total > 0 and skip_total <= skip_margin:
		for _ in range(skip_total):
			read_video_reader_frame(video_reader)

	if not video_reader.get('position') == frame_position:
		refresh_video_reader(video_reader, frame_position)


#todo: needs review - [seeking] [critical: high] kill and respawn per out of order seek, frequent refreshes stack up on random access
def refresh_video_reader(video_reader : VideoReader, frame_position : int) -> None:
	video_reader.get('process').kill()
	video_reader.get('process').wait()
	video_reader['process'] = ffmpeg.create_video_reader(video_reader.get('file_path'), frame_position, video_reader.get('metadata'))
	video_reader['position'] = frame_position


#todo: needs review - [decoding] [critical: high] partial pipe read returns none and desyncs position from the actual stream
def read_video_reader_frame(video_reader : VideoReader) -> Optional[VisionFrame]:
	width, height = video_reader.get('metadata').get('resolution')
	frame_size = width * height * 3
	frame_buffer = video_reader.get('process').stdout.read(frame_size)

	if len(frame_buffer) == frame_size:
		video_reader['position'] = video_reader.get('position') + 1
		return numpy.frombuffer(frame_buffer, numpy.uint8).reshape(height, width, 3)
	return None


#todo: needs review - [memory] [critical: high] frame_set keeps decoded frames in ram, eviction only trims below frame_start minus buffer_margin
def read_video_reader_window(video_reader : VideoReader, frame_start : int, frame_end : int) -> VisionFrameSet:
	source = video_reader.get('file_path')
	frame_set = frame_store.get_frame_store(source)
	buffer_margin = 16

	if frame_start not in frame_set and (frame_start < video_reader.get('position') or frame_start > video_reader.get('position') + buffer_margin):
		refresh_video_reader(video_reader, frame_start)

	for frame_number in range(video_reader.get('position'), frame_end + 1):
		vision_frame = read_video_reader_frame(video_reader)

		if numpy.any(vision_frame):
			frame_store.store_frame(source, frame_number, vision_frame)

	frame_store.evict_frames(source, frame_start - buffer_margin)
	return frame_set


#todo: needs review - [lifecycle] [critical: low] pooled writer keyed by target_path, metadata forwarded by the caller
def get_writer(target_path : str, video_metadata : VideoMetadata, temp_video_fps : Fps, temp_video_resolution : Resolution, output_video_resolution : Resolution, output_video_fps : Fps) -> VideoWriter:
	if target_path not in VIDEO_POOL_SET.get('writer'):
		VIDEO_POOL_SET['writer'][target_path] =\
		{
			'process': ffmpeg.create_video_writer(target_path, temp_video_fps, temp_video_resolution, output_video_resolution, output_video_fps),
			'file_path': target_path,
			'metadata': video_metadata
		}

	return VIDEO_POOL_SET.get('writer').get(target_path)


#todo: needs review - [encoding] [critical: medium] blocking stdin write without backpressure or broken pipe handling
def write_video_writer_frame(video_writer : VideoWriter, vision_frame : VisionFrame) -> None:
	video_writer.get('process').stdin.write(vision_frame.tobytes())


#todo: needs review - [encoding] [critical: medium] encoder failures only surface via returncode at close time
def close_video_writer(video_writer : VideoWriter) -> bool:
	video_writer.get('process').stdin.close()
	video_writer.get('process').wait()
	return video_writer.get('process').returncode == 0


#todo: needs review - [lifecycle] [critical: high] kill over terminate, sigterm deadlocks while the pipe is full
def clear_video_pool() -> None:
	for video_reader in VIDEO_POOL_SET.get('reader').values():
		video_reader.get('process').kill()
		video_reader.get('process').wait()

	for video_writer in VIDEO_POOL_SET.get('writer').values():
		video_writer.get('process').kill()
		video_writer.get('process').wait()

	VIDEO_POOL_SET['reader'].clear()
	VIDEO_POOL_SET['writer'].clear()
	frame_store.clear_frame_store()
