import asyncio
import ctypes
import threading
import time
from collections import deque
from collections.abc import AsyncIterator
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc, rtc_store, session_context, session_manager, state_manager, streamer
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, opus_decoder, opus_encoder, vpx_decoder, vpx_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AomEncoder, AudioCodec, AudioFrame, OpusDecoder, PeerConnection, Resolution, RtcPeer, SdpAnswer, SdpOffer, SessionId, VideoCodec, VisionFrame, VpxDecoder, VpxEncoder


#TODO: needs review
async def process_image(websocket : WebSocket) -> None:
	#TODO: all the websocket handling belongs to the endpoint, these are connection concerns
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		capture_vision_frame = await anext(receive_vision_frames(websocket), None)

		if numpy.any(capture_vision_frame):
			output_vision_frame = streamer.process_frame(create_empty_audio_frame(), capture_vision_frame)
			is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

			if is_success:
				await websocket.send_bytes(output_frame_buffer.tobytes())

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()


#TODO: needs review
def process_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	video_codec : VideoCodec = 'vp8'
	av1_payload_type = rtc.get_payload_type(sdp_offer, 'av1')

	if av1_payload_type:
		video_codec = 'av1'

	video_payload_type = rtc.get_payload_type(sdp_offer, video_codec)

	if not video_payload_type:
		return None

	peer_connection : PeerConnection = rtc.create_peer_connection()
	video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', video_codec, video_payload_type)
	video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', video_codec, video_payload_type)

	audio_codec : AudioCodec = 'opus'
	audio_payload_type = rtc.get_payload_type(sdp_offer, audio_codec)
	audio_receiver_track = None
	audio_sender_track = None

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
			}
		}

		if audio_receiver_track and audio_sender_track:
			rtc_peer['audio'] =\
			{
				'sender_track': audio_sender_track,
				'receiver_track': audio_receiver_track,
				'codec': audio_codec
			}

		rtc_store.init_peers(session_id)
		rtc_store.get_peers(session_id).append(rtc_peer)

		event_loop = asyncio.get_event_loop()
		event_loop.run_in_executor(None, run_peer_loop, session_id, rtc_peer)

	return local_sdp


#TODO: needs review
async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


#TODO: needs review
def run_peer_loop(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	datachannel_library = datachannel_module.create_static_library()
	video_info = rtc_peer.get('video')
	video_codec = video_info.get('codec')
	video_receiver_track = video_info.get('receiver_track')
	audio_info = rtc_peer.get('audio')
	video_receive_buffer = ctypes.create_string_buffer(512 * 1024)
	audio_receive_buffer = ctypes.create_string_buffer(8 * 1024)
	stop_event = threading.Event()
	video_deque : deque = deque(maxlen = 1)
	video_event = threading.Event()
	audio_deque : deque = deque(maxlen = 4)
	audio_receiver = None

	video_receiver = threading.Thread(target = receive_video_into_deque, args = (datachannel_library, video_receiver_track, video_receive_buffer, video_codec, video_deque, video_event, stop_event), daemon = True)
	video_receiver.start()

	if audio_info:
		audio_receiver = threading.Thread(target = receive_audio_into_deque, args = (datachannel_library, audio_info.get('receiver_track'), audio_receive_buffer, audio_deque, stop_event), daemon = True)
		audio_receiver.start()

	video_event.clear()

	if not video_deque:
		if not video_event.wait(timeout = 30.0):
			stop_receiver_threads(stop_event, video_receiver, audio_receiver)
			rtc_store.delete_peers(session_id)
			return

	vision_frame = video_deque.popleft() if video_deque else None

	if vision_frame is None:
		stop_receiver_threads(stop_event, video_receiver, audio_receiver)
		rtc_store.delete_peers(session_id)
		return

	audio_frame = create_empty_audio_frame()
	resolution : Resolution = (vision_frame.shape[1], vision_frame.shape[0])
	video_encoder = create_video_encoder(video_codec, resolution)
	audio_encoder = opus_encoder.create(48000, 2)
	frame_index = 0

	while True:
		if audio_deque:
			audio_frame = audio_deque.popleft()

		output_vision_frame = streamer.process_frame(audio_frame, vision_frame)
		output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])

		if output_resolution != resolution:
			resolution = output_resolution
			destroy_video_encoder(video_codec, video_encoder)
			video_encoder = create_video_encoder(video_codec, resolution)

		raw_vision_frame = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420)
		encoded_video_buffer = bytes()

		if video_codec == 'av1':
			encoded_video_buffer = aom_encoder.encode(video_encoder, raw_vision_frame.tobytes(), resolution, frame_index)
		if video_codec == 'vp8':
			encoded_video_buffer = vpx_encoder.encode(video_encoder, raw_vision_frame.tobytes(), resolution, frame_index)

		now = time.monotonic()

		if encoded_video_buffer:
			rtc.send_video(rtc_peer, encoded_video_buffer, int(now * 90000))

		if audio_encoder and audio_frame.dtype == numpy.float32:
			encoded_audio_buffer = opus_encoder.encode(audio_encoder, audio_frame.tobytes(), 960)

			if encoded_audio_buffer:
				rtc.send_audio(rtc_peer, encoded_audio_buffer, int(now * 48000))

		frame_index += 1

		next_frame = video_deque.popleft() if video_deque else None

		if next_frame is not None:
			vision_frame = next_frame
			continue

		video_event.clear()

		if not video_deque:
			if not video_event.wait(timeout = 30.0):
				break

		next_frame = video_deque.popleft() if video_deque else None

		if next_frame is None:
			break

		vision_frame = next_frame

	stop_receiver_threads(stop_event, video_receiver, audio_receiver)
	destroy_video_encoder(video_codec, video_encoder)
	opus_encoder.destroy(audio_encoder)
	rtc_store.delete_peers(session_id)


def receive_video_into_deque(datachannel_library : ctypes.CDLL, video_track : int, receive_buffer : ctypes.Array[ctypes.c_char], video_codec : VideoCodec, video_deque : deque, video_event : threading.Event, stop_event : threading.Event) -> None:
	video_decoder = create_video_decoder(video_codec)

	while not stop_event.is_set():
		frame_buffer = receive_video_buffer(datachannel_library, video_track, receive_buffer)

		if frame_buffer:
			vision_frame = decode_video_frame(video_codec, video_decoder, frame_buffer)

			if vision_frame is not None:
				video_deque.append(vision_frame)
				video_event.set()
		else:
			stop_event.wait(timeout = 0.001)

	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)
	if video_codec == 'vp8':
		vpx_decoder.destroy(video_decoder)


def receive_audio_into_deque(datachannel_library : ctypes.CDLL, audio_track : int, receive_buffer : ctypes.Array[ctypes.c_char], audio_deque : deque, stop_event : threading.Event) -> None:
	audio_decoder = opus_decoder.create(48000, 2)

	while not stop_event.is_set():
		audio_frame = receive_audio_frame(datachannel_library, audio_track, audio_decoder, receive_buffer)

		if audio_frame.dtype == numpy.float32:
			audio_deque.append(audio_frame)
		else:
			stop_event.wait(timeout = 0.001)

	opus_decoder.destroy(audio_decoder)


def stop_receiver_threads(stop_event : threading.Event, video_receiver : threading.Thread, audio_receiver : Optional[threading.Thread]) -> None:
	stop_event.set()
	video_receiver.join()

	if audio_receiver:
		audio_receiver.join()


#TODO: needs review
def create_video_decoder(video_codec : VideoCodec) -> Optional[VpxDecoder | AomDecoder]:
	if video_codec == 'av1':
		return aom_decoder.create(8)
	if video_codec == 'vp8':
		return vpx_decoder.create(8)

	return None


#TODO: needs review - remove as both are the same
def create_video_encoder(video_codec : VideoCodec, resolution : Resolution) -> Optional[VpxEncoder | AomEncoder]:
	if video_codec == 'av1':
		return aom_encoder.create(resolution, 8000, 8, 10)
	if video_codec == 'vp8':
		return vpx_encoder.create(resolution, 8000, 8, 10)

	return None


#TODO: needs review - remove as this is a trivial helper
def destroy_video_encoder(video_codec : VideoCodec, video_encoder : Optional[VpxEncoder | AomEncoder]) -> None:
	if video_codec == 'av1':
		aom_encoder.destroy(video_encoder)
	if video_codec == 'vp8':
		vpx_encoder.destroy(video_encoder)


def cleanup_peer(session_id : SessionId) -> None:
	rtc_store.delete_peers(session_id)


#TODO: needs review
def receive_audio_frame(datachannel_library : ctypes.CDLL, audio_track : int, audio_decoder : OpusDecoder, receive_buffer : ctypes.Array[ctypes.c_char]) -> AudioFrame:
	buffer_size = ctypes.c_int(8 * 1024)
	receive_output = datachannel_library.rtcReceiveMessage(audio_track, receive_buffer, ctypes.byref(buffer_size))

	if receive_output == 0 and buffer_size.value > 0:
		opus_buffer = receive_buffer.raw[:buffer_size.value]
		output_buffer = opus_decoder.decode(audio_decoder, opus_buffer, 960, 2)

		if output_buffer:
			return numpy.frombuffer(output_buffer, dtype = numpy.float32)

	return create_empty_audio_frame()


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	if video_codec == 'av1':
		aom_pointer = aom_decoder.decode(video_decoder, frame_buffer)
		if aom_pointer:
			frame_width, frame_height = aom_pointer.get('resolution')
			yuv_frame = numpy.frombuffer(aom_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
			return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
	if video_codec == 'vp8':
		vpx_pointer = vpx_decoder.decode(video_decoder, frame_buffer)
		if vpx_pointer:
			frame_width, frame_height = vpx_pointer.get('resolution')
			yuv_frame = numpy.frombuffer(vpx_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
			return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

	return None


def receive_video_buffer(datachannel_library : ctypes.CDLL, video_track : int, receive_buffer : ctypes.Array[ctypes.c_char]) -> Optional[bytes]:
	buffer_size = ctypes.c_int(512 * 1024)
	receive_output = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buffer_size))

	if receive_output == 0 and buffer_size.value > 0:
		return receive_buffer.raw[:buffer_size.value]

	return None
