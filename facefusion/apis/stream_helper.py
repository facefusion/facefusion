import asyncio
from typing import cast

from aiortc import MediaStreamTrack, RTCPeerConnection, VideoStreamTrack
from av import VideoFrame

from facefusion.streamer import process_stream_frame


def create_track(source_track : MediaStreamTrack) -> VideoStreamTrack:
	output_track = VideoStreamTrack()

	async def get_output_frame() -> VideoFrame:
		source_frame = cast(VideoFrame, await source_track.recv())
		output_vision_frame = await asyncio.get_running_loop().run_in_executor(None, process_stream_frame, source_frame.to_ndarray(format = 'bgr24'))
		output_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
		output_frame.pts = source_frame.pts
		output_frame.time_base = source_frame.time_base
		return output_frame

	output_track.recv = get_output_frame
	return output_track


async def on_video_track(rtc_connection : RTCPeerConnection, source_track : MediaStreamTrack) -> None:
	if source_track.kind == 'video':
		output_track = create_track(source_track)
		rtc_connection.addTrack(output_track)
