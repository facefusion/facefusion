import asyncio
import ctypes
import threading
import time
from collections import deque
from collections.abc import AsyncIterator
from functools import partial
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import rtc, rtc_store, streamer
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, opus_decoder, opus_encoder, vpx_decoder, vpx_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AomEncoder, AomPointer, AudioCodec, AudioPack, BitRate, OpusDecoder, PeerConnection, Resolution, RtcPeer, RtcPeerAudio, RtcPeerVideo, SdpAnswer, SdpOffer, SessionId, VideoCodec, VideoPack, VisionFrame, VpxDecoder, VpxEncoder, VpxPointer


async def process_image(websocket : WebSocket) -> None:
	capture_vision_frame = await anext(receive_vision_frames(websocket), None)

	if numpy.any(capture_vision_frame):
		output_vision_frame = streamer.process_frame(create_empty_audio_frame(), capture_vision_frame)
		is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

		if is_success:
			await websocket.send_bytes(output_frame_buffer.tobytes())


#TODO: needs review
def process_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	video_codec : VideoCodec = 'vp8'

	if rtc.get_payload_type(sdp_offer, 'av1'):
		video_codec = 'av1'

	video_payload_type = rtc.get_payload_type(sdp_offer, video_codec)

	if video_payload_type:
		peer_connection : PeerConnection = rtc.create_peer_connection()
		video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', video_codec, video_payload_type)
		video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', video_codec, video_payload_type)
		sender_bitrate = ctypes.c_uint(0)
		rtc.wire_remb(video_sender_track, sender_bitrate)
		receiver_bitrate = ctypes.c_uint(0)
		rtc.wire_remb(video_receiver_track, receiver_bitrate)

		audio_codec : AudioCodec = 'opus'
		audio_payload_type = rtc.get_payload_type(sdp_offer, audio_codec)

		if audio_payload_type:
			audio_receiver_track = rtc.add_audio_track(peer_connection, 'recvonly', audio_codec, audio_payload_type)
			audio_sender_track = rtc.add_audio_track(peer_connection, 'sendonly', audio_codec, audio_payload_type)

		rtc.set_remote_description(peer_connection, sdp_offer)
		local_sdp = rtc.create_sdp_answer(peer_connection)

		if local_sdp:
			rtc_peer : RtcPeer =\
			{
				'peer_connection': peer_connection,
				'video':
				{
					'sender_track': video_sender_track,
					'receiver_track': video_receiver_track,
					'codec': video_codec
				},
				'sender_bitrate': sender_bitrate,
				'receiver_bitrate': receiver_bitrate
			}

			if audio_payload_type:
				rtc_peer['audio'] = RtcPeerAudio(
					sender_track = audio_sender_track,
					receiver_track = audio_receiver_track,
					codec = audio_codec
				)

			rtc_store.init_peers(session_id)
			rtc_store.get_peers(session_id).append(rtc_peer)

			threading.Thread(target = asyncio.run, args = (run_peer_loop(session_id, rtc_peer),), daemon = True).start()
			return local_sdp

		datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)

	return None


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


#TODO: needs review
async def run_peer_loop(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	video_deque : deque[VideoPack] = deque(maxlen = 1)
	audio_deque : deque[AudioPack] = deque(maxlen = 10)
	video_event = threading.Event()

	video_receiver_thread = asyncio.to_thread(receive_video_frames, rtc_peer.get('video'), video_deque, video_event)
	video_encoder_thread = asyncio.to_thread(run_video_encode_loop, rtc_peer, video_deque, video_event)
	coroutines = [ video_receiver_thread, video_encoder_thread ]

	if rtc_peer.get('audio'):
		audio_event = threading.Event()
		coroutines.append(asyncio.to_thread(receive_audio_frames, rtc_peer.get('audio'), audio_deque, audio_event))
		coroutines.append(asyncio.to_thread(run_audio_encode_loop, rtc_peer, audio_deque, audio_event))

	await asyncio.gather(*coroutines)
	rtc_store.delete_peers(session_id)


#TODO: needs review
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


def run_audio_encode_loop(rtc_peer : RtcPeer, audio_deque : deque[AudioPack], audio_event : threading.Event) -> None:
	audio_event.wait()
	audio_event.clear()
	temp_audio_frame, temp_audio_time = audio_deque.popleft()
	audio_encoder = opus_encoder.create(48000, 2)

	while numpy.any(temp_audio_frame):
		output_audio_buffer = opus_encoder.encode(audio_encoder, temp_audio_frame.tobytes(), 960)

		if output_audio_buffer:
			rtc.send_audio(rtc_peer, output_audio_buffer, int(temp_audio_time * 48000))

		if len(audio_deque) == 0:
			audio_event.wait()
			audio_event.clear()

		temp_audio_frame, temp_audio_time = audio_deque.popleft()

	opus_encoder.destroy(audio_encoder)


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


def fill_audio_deque(audio_codec : AudioCodec, audio_decoder : OpusDecoder, audio_buffer : bytes, audio_deque : deque[AudioPack], audio_event : threading.Event) -> None:
	audio_frame = decode_audio_frame(audio_codec, audio_decoder, audio_buffer)

	if audio_frame:
		audio_deque.append((numpy.frombuffer(audio_frame, dtype = numpy.float32), time.monotonic()))
		audio_event.set()


def receive_audio_frames(rtc_peer_audio : RtcPeerAudio, audio_deque : deque[AudioPack], audio_event : threading.Event) -> None:
	audio_track = rtc_peer_audio.get('receiver_track')
	audio_codec = rtc_peer_audio.get('codec')
	datachannel_library = datachannel_module.create_static_library()
	audio_decoder = create_audio_decoder(audio_codec)
	receive_buffer = ctypes.create_string_buffer(8 * 1024)
	available_event = create_event(audio_track, datachannel_library)
	receive_status_code = -3

	while receive_status_code == 0 or receive_status_code == -3:
		buffer_size = ctypes.c_int(8 * 1024)
		receive_status_code = datachannel_library.rtcReceiveMessage(audio_track, receive_buffer, ctypes.byref(buffer_size))

		if receive_status_code == 0 and buffer_size.value > 0:
			audio_buffer = receive_buffer.raw[:buffer_size.value]
			fill_audio_deque(audio_codec, audio_decoder, audio_buffer, audio_deque, audio_event)

		if receive_status_code == -3:
			available_event.wait()
			available_event.clear()

	empty_audio_frame = numpy.empty(0)
	audio_deque.append((empty_audio_frame, 0.0))
	audio_event.set()
	destroy_audio_decoder(audio_codec, audio_decoder)


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


def decode_audio_frame(audio_codec : AudioCodec, audio_decoder : OpusDecoder, input_buffer : bytes) -> Optional[bytes]:
	if audio_codec == 'opus':
		return opus_decoder.decode(audio_decoder, input_buffer, 960, 2)

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


def create_audio_decoder(audio_codec : AudioCodec) -> Optional[OpusDecoder]:
	if audio_codec == 'opus':
		return opus_decoder.create(48000, 2)

	return None


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


def destroy_audio_decoder(audio_codec : AudioCodec, audio_decoder : OpusDecoder) -> None:
	if audio_codec == 'opus':
		opus_decoder.destroy(audio_decoder)


def destroy_video_decoder(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder) -> None:
	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)

	if video_codec == 'vp8':
		vpx_decoder.destroy(video_decoder)


def update_video_encoder_bitrate(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, bitrate : BitRate) -> bool:
	if video_codec == 'av1':
		return aom_encoder.update_bitrate(video_encoder, bitrate)

	if video_codec == 'vp8':
		return vpx_encoder.update_bitrate(video_encoder, bitrate)

	return False


def destroy_video_encoder(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder) -> None:
	if video_codec == 'av1':
		aom_encoder.destroy(video_encoder)

	if video_codec == 'vp8':
		vpx_encoder.destroy(video_encoder)


def destroy_stream(session_id : SessionId) -> bool:
	if rtc_store.has_peers(session_id):
		rtc_store.delete_peers(session_id)
		return not rtc_store.has_peers(session_id)

	return False


def create_event(track : int, datachannel_library : ctypes.CDLL) -> threading.Event:
	available_event = threading.Event()
	available_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(partial(dispatch_event, available_event))
	datachannel_library.rtcSetAvailableCallback(track, available_callback)
	available_event.callback = available_callback  # type: ignore[attr-defined]
	return available_event


def dispatch_event(event : threading.Event, track : int, pointer : ctypes.c_void_p) -> None:
	event.set()
