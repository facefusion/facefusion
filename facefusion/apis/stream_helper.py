import asyncio
from typing import Tuple

from aiortc import MediaStreamTrack, QueuedVideoStreamTrack, RTCPeerConnection, RTCRtpSender
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

from facefusion.streamer import process_vision_frame


def process_stream_frame(target_stream_frame : VideoFrame) -> VideoFrame:
	target_vision_frame = target_stream_frame.to_ndarray(format = 'bgr24')
	output_vision_frame = process_vision_frame(target_vision_frame)
	output_stream_frame = VideoFrame.from_ndarray(output_vision_frame, format = 'bgr24')
	output_stream_frame.pts = target_stream_frame.pts
	output_stream_frame.time_base = target_stream_frame.time_base
	return output_stream_frame


def create_output_track(rtc_connection : RTCPeerConnection, buffer_size : int) -> Tuple[QueuedVideoStreamTrack, RTCRtpSender]:
	output_track = QueuedVideoStreamTrack(buffer_size = buffer_size)
	sender = rtc_connection.addTrack(output_track)
	return output_track, sender


async def process_and_enqueue(target_track : MediaStreamTrack, output_track : QueuedVideoStreamTrack) -> None:
	loop = asyncio.get_running_loop()

	while True:
		try:
			target_stream_frame = await target_track.recv()
		except MediaStreamError:
			pass

		output_stream_frame = await loop.run_in_executor(None, process_stream_frame, target_stream_frame) #type:ignore[arg-type]
		await output_track.put(output_stream_frame)


def on_video_track(rtc_connection : RTCPeerConnection, output_track : QueuedVideoStreamTrack, target_track : MediaStreamTrack) -> None:
	if target_track.kind == 'audio':
		rtc_connection.addTrack(target_track)

	if target_track.kind == 'video':
		asyncio.create_task(process_and_enqueue(target_track, output_track))
