import asyncio
from typing import cast

import numpy
from aiortc import MediaStreamTrack
from av import VideoFrame

from facefusion.streamer import process_stream_frame


async def fill_queue_from_track(temp_track : MediaStreamTrack, queue : asyncio.Queue[VideoFrame]) -> None:
	while True:
		temp_frame = cast(VideoFrame, await temp_track.recv())
		output_vision_frame = process_stream_frame(temp_frame.to_ndarray(format = 'bgr24'))

		if numpy.any(output_vision_frame):
			track_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
			track_frame.pts = temp_frame.pts
			track_frame.time_base = temp_frame.time_base

			if queue.full():
				queue.get_nowait()

			queue.put_nowait(track_frame)


async def on_video_track(queue : asyncio.Queue[VideoFrame], temp_track : MediaStreamTrack) -> None:
	if temp_track.kind == 'video':
		asyncio.create_task(fill_queue_from_track(temp_track, queue))
