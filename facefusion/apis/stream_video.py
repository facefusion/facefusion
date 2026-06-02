import ctypes
import threading
import time
from collections import deque
from typing import Optional

import cv2
import numpy

from facefusion import rtc, streamer
from facefusion.apis.stream_event import create_event
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, vpx_decoder, vpx_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AomEncoder, AomPointer, BitRate, Resolution, RtcPeer, RtcPeerVideo, VideoCodec, VideoPack, VisionFrame, VpxDecoder, VpxEncoder, VpxPointer


def run_video_encode_loop(rtc_peer : RtcPeer, video_deque : deque[VideoPack], video_event : threading.Event) -> None:
	video_event.wait()
	video_event.clear()
	video_codec = rtc_peer.get('video').get('codec')
	temp_vision_frame, temp_video_time = video_deque.popleft()

	if numpy.any(temp_vision_frame):
		temp_resolution : Resolution = (temp_vision_frame.shape[1], temp_vision_frame.shape[0])
		temp_bitrate : BitRate = 8000
		video_encoder = create_video_encoder(video_codec, temp_resolution, temp_bitrate)
		frame_index = 0

		while numpy.any(temp_vision_frame):
			output_vision_frame = streamer.process_frame(create_empty_audio_frame(), temp_vision_frame)
			output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])
			output_vision_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

			peer_bitrate = rtc_peer.get('sender_bitrate').value

			if output_resolution[0] - temp_resolution[0] or output_resolution[1] - temp_resolution[1]:
				destroy_video_encoder(video_codec, video_encoder)
				temp_resolution = output_resolution
				video_encoder = create_video_encoder(video_codec, temp_resolution, temp_bitrate)
				frame_index = 0

			if peer_bitrate and peer_bitrate - temp_bitrate:
				temp_bitrate = peer_bitrate

				if not update_video_encoder_bitrate(video_codec, video_encoder, temp_bitrate):
					destroy_video_encoder(video_codec, video_encoder)
					video_encoder = create_video_encoder(video_codec, temp_resolution, temp_bitrate)
					frame_index = 0

			output_video_buffer = encode_video_frame(video_codec, video_encoder, output_vision_buffer, temp_resolution, frame_index)

			if output_video_buffer:
				rtc.send_video(rtc_peer, output_video_buffer, int(temp_video_time * 90000))

			frame_index += 1
			video_event.wait()
			video_event.clear()
			temp_vision_frame, temp_video_time = video_deque.popleft()

		destroy_video_encoder(video_codec, video_encoder)
		rtc.clear_remb(rtc_peer)


def fill_video_deque(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, video_buffer : bytes, video_deque : deque[VideoPack], video_event : threading.Event) -> None:
	vision_frame = decode_video_frame(video_codec, video_decoder, video_buffer)

	if numpy.any(vision_frame):
		video_deque.append((vision_frame, time.monotonic()))
		video_event.set()


def receive_video_frames(rtc_peer_video : RtcPeerVideo, video_deque : deque[VideoPack], video_event : threading.Event) -> None:
	video_track = rtc_peer_video.get('receiver_track')
	video_codec = rtc_peer_video.get('codec')
	datachannel_library = datachannel_module.create_static_library()
	video_decoder = create_video_decoder(video_codec)
	receive_buffer = ctypes.create_string_buffer(512 * 1024)
	available_event = create_event(video_track, datachannel_library)
	receive_status_code = -3

	while receive_status_code == 0 or receive_status_code == -3:
		buffer_size = ctypes.c_int(512 * 1024)
		receive_status_code = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buffer_size))

		if receive_status_code == 0 and buffer_size.value > 0:
			video_buffer = receive_buffer.raw[:buffer_size.value]
			fill_video_deque(video_codec, video_decoder, video_buffer, video_deque, video_event)

		if receive_status_code == -3:
			available_event.wait()
			available_event.clear()

	empty_vision_frame = numpy.empty(0)
	video_deque.append((empty_vision_frame, 0.0))
	video_event.set()
	destroy_video_decoder(video_codec, video_decoder)


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, input_buffer : bytes) -> Optional[VisionFrame]:
	if video_codec == 'av1':
		aom_pointer = aom_decoder.decode(video_decoder, input_buffer)

		if aom_pointer:
			return normalize_vision_frame(aom_pointer)

	if video_codec == 'vp8':
		vpx_pointer = vpx_decoder.decode(video_decoder, input_buffer)

		if vpx_pointer:
			return normalize_vision_frame(vpx_pointer)

	return None


def encode_video_frame(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, input_buffer : bytes, frame_resolution : Resolution, frame_index : int) -> bytes:
	if video_codec == 'av1':
		return aom_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

	if video_codec == 'vp8':
		return vpx_encoder.encode(video_encoder, input_buffer, frame_resolution, frame_index)

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

	return None


def create_video_encoder(video_codec : VideoCodec, frame_resolution : Resolution, bitrate : BitRate) -> Optional[VpxEncoder | AomEncoder]:
	if video_codec == 'av1':
		return aom_encoder.create(frame_resolution, bitrate, 8, 10)

	if video_codec == 'vp8':
		return vpx_encoder.create(frame_resolution, bitrate, 8, 10)

	return None


def destroy_video_decoder(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder) -> None:
	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)

	if video_codec == 'vp8':
		vpx_decoder.destroy(video_decoder)


def destroy_video_encoder(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder) -> None:
	if video_codec == 'av1':
		aom_encoder.destroy(video_encoder)

	if video_codec == 'vp8':
		vpx_encoder.destroy(video_encoder)


def update_video_encoder_bitrate(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, bitrate : BitRate) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec == 'vp8':
		return vpx_encoder.update_bitrate(video_encoder, bitrate)

	return False
