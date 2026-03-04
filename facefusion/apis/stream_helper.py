import asyncio
from typing import cast

from aiortc import MediaStreamTrack, RTCPeerConnection, VideoStreamTrack
from av import VideoFrame

from facefusion.streamer import process_stream_frame


def create_output_track(target_track : MediaStreamTrack) -> VideoStreamTrack:
	output_track = VideoStreamTrack()

	async def read_stream_frame() -> VideoFrame:
		target_stream_frame = cast(VideoFrame, await target_track.recv())
		output_vision_frame = await asyncio.get_running_loop().run_in_executor(None, process_stream_frame, target_stream_frame.to_ndarray(format = 'bgr24'))
		output_stream_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
		output_stream_frame.pts = target_stream_frame.pts
		output_stream_frame.time_base = target_stream_frame.time_base
		return output_stream_frame

	output_track.recv = read_stream_frame
	return output_track


def on_video_track(rtc_connection : RTCPeerConnection, target_track : MediaStreamTrack) -> None:
	if target_track.kind == 'audio':
		rtc_connection.addTrack(target_track)

	if target_track.kind == 'video':
		output_track = create_output_track(target_track)
		rtc_connection.addTrack(output_track)
