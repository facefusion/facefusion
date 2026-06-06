import ctypes
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from queue import Queue
from typing import Optional

import cv2
import numpy

from facefusion import rtc, state_manager, streamer
from facefusion.apis.stream_event import create_receive_event
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, vp9_decoder, vp9_encoder, vpx_decoder, vpx_encoder
from facefusion.types import AomDecoder, AomEncoder, AomPointer, BitRate, Resolution, RtcPeer, RtcPeerVideo, VideoCodec, VideoPack, VisionFrame, VpxDecoder, VpxEncoder, VpxPointer


def run_video_encode_loop(rtc_peer : RtcPeer, video_queue : Queue[VideoPack]) -> None:
	video_codec = rtc_peer.get('video').get('codec')
	temp_vision_frame, temp_video_time = video_queue.get()

	if numpy.any(temp_vision_frame):
		temp_resolution : Resolution = (temp_vision_frame.shape[1], temp_vision_frame.shape[0])
		temp_bitrate : BitRate = 8000
		video_encoder = create_video_encoder(video_codec, temp_resolution, temp_bitrate)
		previous_video_time = temp_video_time
		temp_deque = deque()
		execution_thread_count = state_manager.get_item('execution_thread_count')
		frame_index = 0

		with ThreadPoolExecutor(max_workers = execution_thread_count) as executor:
			while numpy.any(temp_vision_frame) or temp_deque:

				if numpy.any(temp_vision_frame) and len(temp_deque) < execution_thread_count:
					temp_deque.append((executor.submit(process_video_frame, temp_vision_frame), temp_video_time))
					temp_vision_frame, temp_video_time = video_queue.get()

				else:
					output_future, output_video_time = temp_deque.popleft()
					encode_start = time.monotonic()
					output_vision_buffer, output_resolution = output_future.result()
					peer_bitrate : BitRate = rtc_peer.get('sender_bitrate').value
					video_encoder, temp_resolution, temp_bitrate, frame_index = adapt_video_encoder(video_codec, video_encoder, temp_resolution, temp_bitrate, output_resolution, peer_bitrate, frame_index)
					output_video_buffer = encode_video_frame(video_codec, video_encoder, output_vision_buffer, temp_resolution, frame_index)

					if output_video_buffer:
						rtc.send_video(rtc_peer, output_video_buffer, int(output_video_time * 90000))

					encode_time = time.monotonic() - encode_start
					frame_interval = output_video_time - previous_video_time
					previous_video_time = output_video_time

					rtc.adapt_receiver_bitrate(rtc_peer, calculate_receiver_bitrate(rtc_peer, encode_time, frame_interval))
					frame_index += 1

		destroy_video_encoder(video_codec, video_encoder)
		rtc.clear_bitrate(rtc_peer)


def receive_video_frames(rtc_peer_video : RtcPeerVideo, video_queue : Queue[VideoPack]) -> None:
	video_track = rtc_peer_video.get('receiver_track')
	video_codec = rtc_peer_video.get('codec')
	video_decoder = create_video_decoder(video_codec)

	video_frame_handler = partial(handle_video_frame, video_codec, video_decoder, video_queue)
	receive_event = create_receive_event(video_track, video_frame_handler)
	receive_event.wait()
	empty_vision_frame = numpy.empty(0)
	video_queue.put((empty_vision_frame, 0.0))
	destroy_video_decoder(video_codec, video_decoder)


def process_video_frame(vision_frame : VisionFrame) -> tuple[bytes, Resolution]:
	output_vision_frame = streamer.process_frame(create_empty_audio_frame(), vision_frame)
	output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])
	output_vision_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	return output_vision_buffer, output_resolution


def adapt_video_encoder(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, resolution : Resolution, bitrate : BitRate, output_resolution : Resolution, peer_bitrate : BitRate, frame_index : int) -> tuple[VpxEncoder | AomEncoder, Resolution, BitRate, int]:
	if output_resolution[0] - resolution[0] or output_resolution[1] - resolution[1]:
		destroy_video_encoder(video_codec, video_encoder)
		resolution = output_resolution
		video_encoder = create_video_encoder(video_codec, resolution, bitrate)
		frame_index = 0

	if peer_bitrate and peer_bitrate - bitrate:
		bitrate = peer_bitrate

		if not update_video_encoder_bitrate(video_codec, video_encoder, bitrate):
			destroy_video_encoder(video_codec, video_encoder)
			video_encoder = create_video_encoder(video_codec, resolution, bitrate)
			frame_index = 0

	return video_encoder, resolution, bitrate, frame_index


def calculate_receiver_bitrate(rtc_peer : RtcPeer, encode_time : float, frame_interval : float) -> BitRate:
	min_bitrate : BitRate = 500
	max_bitrate : BitRate = 8000
	bitrate : BitRate = rtc_peer.get('receiver_bitrate').value

	if frame_interval > 0:
		scale = frame_interval / encode_time
		bitrate = int(bitrate * scale)
		bitrate = max(min_bitrate, min(max_bitrate, bitrate))

	return bitrate


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, input_buffer : bytes) -> Optional[VisionFrame]:
	if video_codec == 'av1':
		aom_pointer = aom_decoder.decode(video_decoder, input_buffer)

		if aom_pointer:
			return normalize_vision_frame(aom_pointer)

	if video_codec == 'vp8':
		vpx_pointer = vpx_decoder.decode(video_decoder, input_buffer)

		if vpx_pointer:
			return normalize_vision_frame(vpx_pointer)

	if video_codec == 'vp9':
		vpx_pointer = vp9_decoder.decode(video_decoder, input_buffer)

		if vpx_pointer:
			return normalize_vision_frame(vpx_pointer)

	return None


def encode_video_frame(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, input_buffer : bytes, frame_resolution : Resolution, frame_index : int) -> bytes:
	if video_codec == 'av1':
		return aom_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	if video_codec == 'vp8':
		return vpx_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	if video_codec == 'vp9':
		return vp9_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	return bytes()


def normalize_vision_frame(frame_pointer : AomPointer | VpxPointer) -> VisionFrame:
	frame_width, frame_height = frame_pointer.get('resolution')
	vision_frame = numpy.frombuffer(frame_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
	return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)


def create_video_decoder(video_codec : VideoCodec) -> Optional[VpxDecoder | AomDecoder]:
	if video_codec == 'av1':
		return aom_decoder.create(8)

	if video_codec == 'vp8':
		return vpx_decoder.create(8)

	if video_codec == 'vp9':
		return vp9_decoder.create(8)

	return None


def create_video_encoder(video_codec : VideoCodec, frame_resolution : Resolution, bitrate : BitRate) -> Optional[VpxEncoder | AomEncoder]:
	if video_codec == 'av1':
		return aom_encoder.create(frame_resolution, bitrate, 8, 10)

	if video_codec == 'vp8':
		return vpx_encoder.create(frame_resolution, bitrate, 8, 10)

	if video_codec == 'vp9':
		return vp9_encoder.create(frame_resolution, bitrate, 8, 10)

	return None


def destroy_video_decoder(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder) -> None:
	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)

	if video_codec == 'vp8':
		vpx_decoder.destroy(video_decoder)

	if video_codec == 'vp9':
		vp9_decoder.destroy(video_decoder)


def destroy_video_encoder(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder) -> None:
	if video_codec == 'av1':
		aom_encoder.destroy(video_encoder)

	if video_codec == 'vp8':
		vpx_encoder.destroy(video_encoder)

	if video_codec == 'vp9':
		vp9_encoder.destroy(video_encoder)


def update_video_encoder_bitrate(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, bitrate : BitRate) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec == 'vp8':
		return vpx_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec == 'vp9':
		return vp9_encoder.update_bitrate(video_encoder, bitrate)

	return False


def handle_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, video_queue : Queue[VideoPack], track : int, data : ctypes.c_void_p, size : int, info : ctypes.c_void_p, pointer : ctypes.c_void_p) -> None:
	video_buffer = ctypes.string_at(data, size)
	vision_frame = decode_video_frame(video_codec, video_decoder, video_buffer)

	if numpy.any(vision_frame):
		if video_queue.full():
			video_queue.get_nowait()

		video_queue.put((vision_frame, time.monotonic()))
