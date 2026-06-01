import ctypes
import threading
import time
from collections import deque
from functools import partial
from typing import Optional

import cv2
import numpy

from facefusion.apis.stream_manager import dispatch_event
from facefusion.codecs import aom_decoder, aom_encoder, vpx_decoder, vpx_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AomEncoder, AomPointer, BitRate, Resolution, RtcPeerVideo, VideoCodec, VideoPack, VisionFrame, VpxDecoder, VpxEncoder, VpxPointer


def receive_video_frames(rtc_peer_video : RtcPeerVideo, video_deque : deque[VideoPack], video_event : threading.Event) -> None:
	video_track = rtc_peer_video.get('receiver_track')
	video_codec = rtc_peer_video.get('codec')
	datachannel_library = datachannel_module.create_static_library()
	video_decoder = create_video_decoder(video_codec)
	receive_buffer = ctypes.create_string_buffer(512 * 1024)
	available_event = threading.Event()
	available_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(partial(dispatch_event, available_event))
	datachannel_library.rtcSetAvailableCallback(video_track, available_callback)
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


def update_video_encoder_bitrate(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, bitrate : BitRate) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec == 'vp8':
		return vpx_encoder.update_bitrate(video_encoder, bitrate)

	return False


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


def fill_video_deque(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, video_buffer : bytes, video_deque : deque[VideoPack], video_event : threading.Event) -> None:
	vision_frame = decode_video_frame(video_codec, video_decoder, video_buffer)

	if numpy.any(vision_frame):
		video_deque.append((vision_frame, time.monotonic()))
		video_event.set()


def normalize_vision_frame(frame_pointer : AomPointer | VpxPointer) -> VisionFrame:
	frame_width, frame_height = frame_pointer.get('resolution')
	vision_frame = numpy.frombuffer(frame_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
	return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)
