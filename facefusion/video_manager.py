import uuid
from typing import Optional

import numpy

from facefusion import ffmpeg, ffprobe, frame_store
from facefusion.common_helper import get_first, get_last
from facefusion.types import Fps, Resolution, VideoPoolSet, VideoReader, VideoWriter, VisionFrame, VisionFrameSet

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
			'id': uuid.uuid4().hex,
			'file_path': video_path,
			'process': ffmpeg.create_video_reader(video_path, 0, video_metadata),
			'metadata': video_metadata,
			'position': 0
		}

	return VIDEO_POOL_SET.get('reader').get(video_path)


#todo: needs review - [seeking] [critical: high] forward skip up to 128 frames by draining the pipe, everything else refreshes the process
def conditional_set_video_reader_position(video_reader : VideoReader, frame_position : int) -> None:
	skip_total = frame_position - video_reader.get('position')
	skip_margin = 128

	if 0 < skip_total <= skip_margin:
		for _ in range(skip_total):
			read_video_reader_frame(video_reader)

	if not video_reader.get('position') == frame_position:
		refresh_video_reader(video_reader, frame_position)


def refresh_video_reader(video_reader : VideoReader, frame_position : int) -> None:
	close_video_reader(video_reader)

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
	id = video_reader.get('id')
	frame_set = frame_store.get_frame_store(id)
	buffer_margin = 16
	keep_margin = 4
	frame_gaps = []

	for frame_index in range(frame_start, frame_end + 1):
		if frame_index not in frame_set:
			frame_gaps.append(frame_index)

	if frame_gaps:
		frame_position = get_first(frame_gaps)
		skip_total = frame_position - video_reader.get('position')

		if skip_total < 0 or skip_total > buffer_margin:
			refresh_video_reader(video_reader, frame_position)

		for decode_index in range(video_reader.get('position'), get_last(frame_gaps) + 1):
			vision_frame = read_video_reader_frame(video_reader)

			if numpy.any(vision_frame):
				frame_store.set_frame(id, decode_index, vision_frame)

	frame_store.reduce_frames(id, frame_start - keep_margin, frame_end + keep_margin)
	return frame_store.select_frame_set(id, frame_start, frame_end)


def close_video_reader(video_reader : VideoReader) -> None:
	video_reader.get('process').kill()
	video_reader.get('process').wait()
	frame_store.clear_frames(video_reader.get('id'))


def get_writer(target_path : str, temp_video_fps : Fps, temp_video_resolution : Resolution, output_video_resolution : Resolution, output_video_fps : Fps) -> VideoWriter:
	if target_path not in VIDEO_POOL_SET.get('writer'):
		VIDEO_POOL_SET['writer'][target_path] =\
		{
			'id': uuid.uuid4().hex,
			'file_path': target_path,
			'process': ffmpeg.create_video_writer(target_path, temp_video_fps, temp_video_resolution, output_video_resolution, output_video_fps),
			'metadata':
			{
				'fps': output_video_fps,
				'resolution': output_video_resolution,
			}
		}

	return VIDEO_POOL_SET.get('writer').get(target_path)


def write_video_writer(video_writer : VideoWriter, vision_frame : VisionFrame) -> None:
	video_writer.get('process').stdin.write(vision_frame.tobytes())


def close_video_writer(video_writer : VideoWriter) -> bool:
	video_writer.get('process').stdin.close()
	video_writer.get('process').wait()

	return video_writer.get('process').returncode == 0


def clear_video_pool() -> None:
	for video_reader in VIDEO_POOL_SET.get('reader').values():
		close_video_reader(video_reader)

	for video_writer in VIDEO_POOL_SET.get('writer').values():
		close_video_writer(video_writer)

	VIDEO_POOL_SET['reader'].clear()
	VIDEO_POOL_SET['writer'].clear()
