import ctypes
import time
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from queue import Queue
from typing import Optional, Tuple

import cv2
import numpy

from facefusion import rtc, streamer
from facefusion.apis.stream_event import create_receive_event
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, vpx_decoder, vpx_encoder
from facefusion.types import AomDecoder, AomEncoder, BitRate, Buffer, BufferPack, Resolution, RtcPeer, RtcPeerVideo, Time, VideoCodec, VisionFrame, VpxDecoder, VpxEncoder


def run_video_encode_loop(rtc_peer : RtcPeer, video_queue : Queue[Tuple[Time, Future[BufferPack]]]) -> None:
	video_codec = rtc_peer.get('video').get('codec')
	video_time, video_future = video_queue.get()
	video_pack = video_future.result()
	video_buffer = video_pack.get('buffer')
	video_resolution = video_pack.get('resolution')

	if video_buffer:
		temp_resolution : Resolution = video_resolution
		temp_bitrate : BitRate = 8000
		video_encoder = create_video_encoder(video_codec, temp_resolution, temp_bitrate)
		temp_video_time = video_time
		frame_index = 0

		while video_buffer:
			encode_start = time.monotonic()
			sender_bitrate = calculate_sender_bitrate(rtc_peer, temp_bitrate)

			if video_resolution[0] - temp_resolution[0] or video_resolution[1] - temp_resolution[1]:
				temp_resolution = video_resolution
				update_video_encoder_resolution(video_codec, video_encoder, temp_resolution)

			if sender_bitrate - temp_bitrate:
				temp_bitrate = sender_bitrate
				update_video_encoder_bitrate(video_codec, video_encoder, temp_bitrate)

			__video_buffer__ = encode_video_frame(video_codec, video_encoder, video_buffer, temp_resolution, frame_index)

			if __video_buffer__:
				video_timestamp = int(video_time * 90000)
				rtc.send_video(rtc_peer, __video_buffer__, video_timestamp)

			encode_time = time.monotonic() - encode_start
			frame_interval = video_time - temp_video_time
			temp_video_time = video_time

			receiver_bitrate = calculate_receiver_bitrate(rtc_peer, encode_time, frame_interval)
			rtc.adapt_receiver_bitrate(rtc_peer, receiver_bitrate)
			frame_index += 1

			video_time, video_future = video_queue.get()
			video_pack = video_future.result()
			video_buffer = video_pack.get('buffer')
			video_resolution = video_pack.get('resolution')

		destroy_video_encoder(video_codec, video_encoder)
		rtc.clear_bitrate(rtc_peer)


def receive_video_frames(rtc_peer_video : RtcPeerVideo, video_queue : Queue[Tuple[Time, Future[BufferPack]]], video_executor : ThreadPoolExecutor) -> None:
	video_track = rtc_peer_video.get('receiver_track')
	video_codec = rtc_peer_video.get('codec')
	video_decoder = create_video_decoder(video_codec)

	video_frame_handler = partial(handle_video_frame, video_codec, video_decoder, video_queue, video_executor)
	receive_event = create_receive_event(video_track, video_frame_handler)
	receive_event.wait()

	empty_future : Future[BufferPack] = Future()
	empty_future.set_result(BufferPack(buffer = bytes(), resolution = (0, 0)))
	video_queue.put((0.0, empty_future))
	destroy_video_decoder(video_codec, video_decoder)


def process_video_frame(input_vision_frame : VisionFrame) -> BufferPack:
	output_vision_frame = streamer.process_frame(create_empty_audio_frame(), input_vision_frame)
	output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])
	output_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	return BufferPack(buffer = output_buffer, resolution = output_resolution)


def calculate_receiver_bitrate(rtc_peer : RtcPeer, encode_time : float, frame_interval : float) -> BitRate:
	min_bitrate : BitRate = 500
	max_bitrate : BitRate = 8000
	bitrate : BitRate = rtc_peer.get('receiver_bitrate').value

	if frame_interval > 0:
		scale = frame_interval / encode_time
		bitrate = int(bitrate * scale)
		bitrate = max(min_bitrate, min(max_bitrate, bitrate))

	return bitrate


#todo: does not feel final as this is an clamp and not calculate
def calculate_sender_bitrate(rtc_peer : RtcPeer, bitrate : BitRate) -> BitRate:
	min_bitrate : BitRate = 500
	max_bitrate : BitRate = 8000
	peer_bitrate : BitRate = rtc_peer.get('sender_bitrate').value

	if peer_bitrate > 0:
		bitrate = max(min_bitrate, min(max_bitrate, peer_bitrate))

	return bitrate


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, input_buffer : Buffer) -> Optional[VisionFrame]:
	if video_codec == 'av1':
		aom_pointer = aom_decoder.decode(video_decoder, input_buffer)

		if aom_pointer:
			return normalize_vision_frame(aom_pointer)

	if video_codec in [ 'vp8', 'vp9' ]:
		vpx_pointer = vpx_decoder.decode(video_decoder, input_buffer)

		if vpx_pointer:
			return normalize_vision_frame(vpx_pointer)

	return None


def encode_video_frame(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, input_buffer : Buffer, frame_resolution : Resolution, frame_index : int) -> Buffer:
	if video_codec == 'av1':
		return aom_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	if video_codec in [ 'vp8', 'vp9' ]:
		return vpx_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	return bytes()


def normalize_vision_frame(frame_pointer : BufferPack) -> VisionFrame:
	frame_width, frame_height = frame_pointer.get('resolution')
	vision_frame = numpy.frombuffer(frame_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
	return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)


def create_video_decoder(video_codec : VideoCodec) -> Optional[VpxDecoder | AomDecoder]:
	if video_codec == 'av1':
		return aom_decoder.create(8)

	if video_codec in [ 'vp8', 'vp9' ]:
		return vpx_decoder.create(video_codec, 8)

	return None


def create_video_encoder(video_codec : VideoCodec, frame_resolution : Resolution, bitrate : BitRate) -> Optional[VpxEncoder | AomEncoder]:
	if video_codec == 'av1':
		return aom_encoder.create(frame_resolution, bitrate, 8, 10)

	if video_codec in [ 'vp8', 'vp9' ]:
		return vpx_encoder.create(video_codec, frame_resolution, bitrate, 8, 10)

	return None


def destroy_video_decoder(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder) -> None:
	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)

	if video_codec in [ 'vp8', 'vp9' ]:
		vpx_decoder.destroy(video_decoder)


def destroy_video_encoder(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder) -> None:
	if video_codec == 'av1':
		aom_encoder.destroy(video_encoder)

	if video_codec in [ 'vp8', 'vp9' ]:
		vpx_encoder.destroy(video_encoder)


def update_video_encoder_resolution(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, frame_resolution : Resolution) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_resolution(video_encoder, frame_resolution)

	if video_codec in [ 'vp8', 'vp9' ]:
		return vpx_encoder.update_resolution(video_encoder, frame_resolution)

	return False


def update_video_encoder_bitrate(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, bitrate : BitRate) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec in [ 'vp8', 'vp9' ]:
		return vpx_encoder.update_bitrate(video_encoder, bitrate)

	return False


#todo: we can remove the dead args or pass audio buffer
def handle_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, video_queue : Queue[Tuple[Time, Future[BufferPack]]], video_executor : ThreadPoolExecutor, track : int, data : ctypes.c_void_p, size : int, info : ctypes.c_void_p, pointer : ctypes.c_void_p) -> None:
	video_buffer = ctypes.string_at(data, size)
	vision_frame = decode_video_frame(video_codec, video_decoder, video_buffer)

	if numpy.any(vision_frame) and video_queue.qsize() < video_queue.maxsize:
		video_future = video_executor.submit(process_video_frame, vision_frame)
		video_queue.put((time.monotonic(), video_future))
