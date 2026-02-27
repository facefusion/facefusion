import asyncio
from typing import Any

import numpy
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

from facefusion.streamer import process_stream_frame
from facefusion.types import FrameQueue


async def get_from_queue(queue : FrameQueue) -> Any:
	return await queue.get()


async def process_video_track(track : Any, queue : FrameQueue) -> None:
	try:
		while True:
			track_frame = await track.recv()
			output_vision_frame = process_stream_frame(track_frame.to_ndarray(format = 'bgr24'))

			if numpy.any(output_vision_frame):
				output_track_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
				output_track_frame.pts = track_frame.pts
				output_track_frame.time_base = track_frame.time_base

				if queue.full():
					queue.get_nowait()

				queue.put_nowait(output_track_frame)
	except (MediaStreamError, asyncio.CancelledError):
		pass


async def on_video_track(queue : FrameQueue, track : Any) -> None:
	if track.kind == 'video':
		asyncio.create_task(process_video_track(track, queue))
