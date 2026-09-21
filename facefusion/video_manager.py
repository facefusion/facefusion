import hashlib
import uuid
from io import BufferedReader
from typing import Optional, cast

import numpy

from facefusion import ffmpeg, ffprobe, frame_store, store_creator, vision
from facefusion.common_helper import get_first, get_last
from facefusion.session_context import get_session_id
from facefusion.types import Fps, Resolution, SessionId, Store, VideoReader, VideoWriter, VisionFrame, VisionFrameSet

VIDEO_POOL_STORE : Store = store_creator.create_store(
{
	'reader': {},
	'writer': {}
})


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(VIDEO_POOL_STORE, session_id)


def get_reader(video_path : str, context : str) -> VideoReader:
	session_id = get_session_id()
	reader_id = hashlib.sha1((video_path + '_' + context + '_' + session_id).encode()).hexdigest()
	video_pool = store_creator.get_content(VIDEO_POOL_STORE, session_id)

	if reader_id not in video_pool.get('reader'):
		video_metadata = ffprobe.extract_static_video_metadata(video_path)

		video_pool['reader'][reader_id] =\
		{
			'id': reader_id,
			'file_path': video_path,
			'process': ffmpeg.create_video_reader(video_path, 0, video_metadata),
			'metadata': video_metadata,
			'frame_index': 0
		}

	return video_pool.get('reader').get(reader_id)


def conditional_seek_video_reader(video_reader : VideoReader, frame_index : int = 0) -> None:
	frame_total = video_reader.get('metadata').get('frame_total')
	frame_index = min(frame_total - 1, frame_index)
	skip_total = frame_index - video_reader.get('frame_index')
	skip_margin = 128

	if 0 < skip_total <= skip_margin:
		drain_video_reader(video_reader, skip_total)

	if not video_reader.get('frame_index') == frame_index:
		seek_video_reader(video_reader, frame_index)


def seek_video_reader(video_reader : VideoReader, frame_index : int = 0) -> None:
	close_video_reader(video_reader)

	video_reader['process'] = ffmpeg.create_video_reader(video_reader.get('file_path'), frame_index, video_reader.get('metadata'))
	video_reader['frame_index'] = frame_index


def drain_video_reader(video_reader : VideoReader, skip_total : int) -> None:
	width, height = video_reader.get('metadata').get('resolution')
	channel_total = 3
	frame_size = width * height * channel_total

	for _ in range(skip_total):
		video_reader.get('process').stdout.read(frame_size)

	video_reader['frame_index'] = video_reader.get('frame_index') + skip_total


def read_video_frame(video_reader : VideoReader) -> Optional[VisionFrame]:
	width, height = video_reader.get('metadata').get('resolution')
	channel_total = 3
	video_stream = cast(BufferedReader, video_reader.get('process').stdout)
	vision_frame = numpy.empty(width * height * channel_total, numpy.uint8)

	if video_stream.readinto(vision_frame) == vision_frame.size:
		video_reader['frame_index'] = video_reader.get('frame_index') + 1
		return vision_frame.reshape(height, width, channel_total)

	return None


def read_video_frames(video_reader : VideoReader, frame_start : int, frame_end : int) -> VisionFrameSet:
	reader_id = video_reader.get('id')
	frame_set = frame_store.get_frame_store(reader_id)
	keep_margin = 4
	frame_gaps = []

	for frame_index in range(frame_start, frame_end + 1):
		if frame_index not in frame_set:
			frame_gaps.append(frame_index)

	if frame_gaps:
		collect_video_frames(video_reader, get_first(frame_gaps), get_last(frame_gaps))

	frame_store.reduce_frames(reader_id, frame_start - keep_margin, frame_end + keep_margin)
	return frame_store.select_frame_set(reader_id, frame_start, frame_end)


def collect_video_frames(video_reader : VideoReader, frame_start : int, frame_end : int) -> None:
	reader_id = video_reader.get('id')
	skip_total = frame_start - video_reader.get('frame_index')
	skip_margin = 16

	if skip_total < 0 or skip_total > skip_margin:
		seek_video_reader(video_reader, frame_start)

	for frame_index in range(video_reader.get('frame_index'), frame_end + 1):
		vision_frame = read_video_frame(video_reader)

		if vision.is_vision_frame(vision_frame):
			frame_store.set_frame(reader_id, frame_index, vision_frame)


def close_video_reader(video_reader : VideoReader) -> None:
	video_reader.get('process').kill()
	video_reader.get('process').wait()


def get_writer(video_path : str, temp_video_fps : Fps, temp_video_resolution : Resolution, output_video_resolution : Resolution, output_video_fps : Fps) -> VideoWriter:
	session_id = get_session_id()
	video_pool = store_creator.get_content(VIDEO_POOL_STORE, session_id)

	if video_path not in video_pool.get('writer'):
		video_pool['writer'][video_path] =\
		{
			'id': uuid.uuid4().hex,
			'file_path': video_path,
			'process': ffmpeg.create_video_writer(video_path, temp_video_fps, temp_video_resolution, output_video_resolution, output_video_fps),
			'metadata':
			{
				'fps': output_video_fps,
				'resolution': output_video_resolution
			}
		}

	return video_pool.get('writer').get(video_path)


def write_video_frame(video_writer : VideoWriter, vision_frame : VisionFrame) -> None:
	video_writer.get('process').stdin.write(vision_frame.data)


def close_video_writer(video_writer : VideoWriter) -> bool:
	video_writer.get('process').stdin.close()
	video_writer.get('process').wait()

	return video_writer.get('process').returncode == 0


def clear() -> None:
	session_id = get_session_id()
	video_pool = store_creator.get_content(VIDEO_POOL_STORE, session_id)

	for video_reader in video_pool.get('reader').values():
		close_video_reader(video_reader)
		frame_store.clear_frames(video_reader.get('id'))

	for video_writer in video_pool.get('writer').values():
		close_video_writer(video_writer)

	store_creator.init_content(VIDEO_POOL_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	video_pool = store_creator.get_content(VIDEO_POOL_STORE, session_id)

	if video_pool:
		for video_reader in video_pool.get('reader').values():
			close_video_reader(video_reader)
			frame_store.clear_frames(video_reader.get('id'))

		for video_writer in video_pool.get('writer').values():
			close_video_writer(video_writer)

	store_creator.delete_content(VIDEO_POOL_STORE, session_id)
