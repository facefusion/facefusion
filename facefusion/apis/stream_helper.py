import asyncio
from typing import cast

import numpy
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

from facefusion.streamer import process_stream_frame


async def process_video_track(track : MediaStreamTrack, queue : asyncio.Queue[VideoFrame]) -> None:
	try:
		while True:
			temp_frame = cast(VideoFrame, await track.recv())
			output_vision_frame = process_stream_frame(temp_frame.to_ndarray(format = 'bgr24'))

			if numpy.any(output_vision_frame):
				track_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
				track_frame.pts = temp_frame.pts
				track_frame.time_base = temp_frame.time_base

				if queue.full():
					queue.get_nowait()

				queue.put_nowait(track_frame)
	except (MediaStreamError, asyncio.CancelledError):
		pass


async def on_video_track(queue : asyncio.Queue[VideoFrame], track : MediaStreamTrack) -> None:
	if track.kind == 'video':
		asyncio.create_task(process_video_track(track, queue))
