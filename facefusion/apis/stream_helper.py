import asyncio
import ctypes
import time
from collections.abc import AsyncIterator
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc, rtc_store, session_context, session_manager, state_manager, streamer
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs.aom import create_aom_decoder, create_aom_encoder, decode_aom_buffer, destroy_aom_decoder, destroy_aom_encoder, encode_aom_buffer
from facefusion.codecs.opus import create_opus_decoder, create_opus_encoder, decode_opus_buffer, destroy_opus_decoder, destroy_opus_encoder, encode_opus_buffer
from facefusion.codecs.vpx import create_vpx_decoder, create_vpx_encoder, decode_vpx_buffer, destroy_vpx_decoder, destroy_vpx_encoder, encode_vpx_buffer
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AudioFrame, OpusDecoder, PeerConnection, Resolution, RtcPeer, SdpAnswer, SdpOffer, SessionId, VideoCodec, VisionFrame, VpxDecoder


async def process_image(websocket : WebSocket) -> None:
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


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


def process_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	sdp_media = rtc.detect_sdp_media(sdp_offer)
	video_media = sdp_media.get('video')

	if not video_media:
		return None

	peer_connection : PeerConnection = rtc.create_peer_connection()

	video_codec = video_media.get('codec')
	video_payload_type = video_media.get('payload_type')
	video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', video_codec, video_payload_type, b'0', 44)
	video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', video_codec, video_payload_type, b'1', 42)

	audio_media = sdp_media.get('audio')
	audio_receiver_track = None
	audio_sender_track = None

	if audio_media:
		audio_codec = audio_media.get('codec')
		audio_payload_type = audio_media.get('payload_type')
		audio_receiver_track = rtc.add_audio_track(peer_connection, 'recvonly', audio_codec, audio_payload_type, b'2', 45)
		audio_sender_track = rtc.add_audio_track(peer_connection, 'sendonly', audio_codec, audio_payload_type, b'3', 43)

	rtc.set_remote_description(peer_connection, sdp_offer)
	local_sdp = rtc.create_sdp_answer(peer_connection)

	if local_sdp:
		rtc_peer : RtcPeer =\
		{
			'peer_connection': peer_connection,
			'video':\
			{
				'sender_track': video_sender_track,
				'receiver_track': video_receiver_track,
				'codec': video_codec,
			}
		}

		if audio_receiver_track and audio_sender_track and audio_media:
			rtc_peer['audio'] =\
			{
				'sender_track': audio_sender_track,
				'receiver_track': audio_receiver_track,
				'codec': audio_media.get('codec'),
			}

		rtc_store.add_peer(session_id, rtc_peer)

		event_loop = asyncio.get_event_loop()
		event_loop.run_in_executor(None, run_peer_loop, session_id, rtc_peer)

	return local_sdp


def run_peer_loop(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	datachannel_library = datachannel_module.create_static_library()
	video_info = rtc_peer.get('video')
	video_track = video_info.get('receiver_track')
	video_codec = video_info.get('codec')
	video_decoder = create_video_decoder(video_codec)
	audio_info = rtc_peer.get('audio')
	audio_track = audio_info.get('receiver_track') if audio_info else None
	audio_decoder = create_opus_decoder(48000, 2) if audio_info else None
	video_receive_buffer = ctypes.create_string_buffer(512 * 1024)
	audio_receive_buffer = ctypes.create_string_buffer(8 * 1024)

	vision_frame = poll_for_frame(datachannel_library, video_track, video_codec, video_decoder, video_receive_buffer, 30.0)

	if vision_frame is None:
		cleanup_peer(session_id, rtc_peer, video_codec, video_decoder, audio_decoder)
		return

	resolution : Resolution = (vision_frame.shape[1], vision_frame.shape[0])
	audio_frame = create_empty_audio_frame()
	video_encoder = create_video_encoder(video_codec, resolution)
	opus_encoder = create_opus_encoder(48000, 2)
	frame_index = 0

	while True:
		if audio_track and audio_decoder:
			audio_frame = receive_audio_frame(datachannel_library, audio_track, audio_decoder, audio_receive_buffer)

		output_vision_frame = streamer.process_frame(audio_frame, vision_frame)
		output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])

		if output_resolution != resolution:
			resolution = output_resolution
			destroy_video_encoder(video_codec, video_encoder)
			video_encoder = create_video_encoder(video_codec, resolution)

		yuv_frame = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420)

		if video_codec == 'av1':
			encoded_video_buffer = encode_aom_buffer(video_encoder, yuv_frame.tobytes(), resolution, frame_index)
		if video_codec == 'vp8':
			encoded_video_buffer = encode_vpx_buffer(video_encoder, yuv_frame.tobytes(), resolution, frame_index)

		if encoded_video_buffer:
			video_timestamp = int(time.monotonic() * 90000)
			rtc.send_video(rtc_peer, encoded_video_buffer, video_timestamp)

		if opus_encoder and audio_frame is not None and audio_frame.size > 0:
			encoded_audio_buffer = encode_opus_buffer(opus_encoder, audio_frame.tobytes(), 960)

			if encoded_audio_buffer:
				audio_timestamp = int(time.monotonic() * 48000)
				rtc.send_audio(rtc_peer, encoded_audio_buffer, audio_timestamp)

		frame_index += 1

		next_frame = drain_to_latest_frame(datachannel_library, video_track, video_codec, video_decoder, video_receive_buffer)

		if next_frame is not None:
			vision_frame = next_frame
			continue

		next_frame = poll_for_frame(datachannel_library, video_track, video_codec, video_decoder, video_receive_buffer, 30.0)

		if next_frame is None:
			break

		vision_frame = next_frame

	destroy_video_encoder(video_codec, video_encoder)
	destroy_opus_encoder(opus_encoder)
	cleanup_peer(session_id, rtc_peer, video_codec, video_decoder, audio_decoder)


def cleanup_peer(session_id : SessionId, rtc_peer : RtcPeer, video_codec : str, video_decoder, audio_decoder) -> None:
	if video_decoder:
		if video_codec == 'av1':
			destroy_aom_decoder(video_decoder)
		if video_codec == 'vp8':
			destroy_vpx_decoder(video_decoder)

	if audio_decoder:
		destroy_opus_decoder(audio_decoder)

	rtc_store.delete_peer(session_id, rtc_peer.get('peer_connection'))


def create_video_decoder(video_codec : VideoCodec) -> Optional[VpxDecoder | AomDecoder]:
	if video_codec == 'av1':
		return create_aom_decoder()
	if video_codec == 'vp8':
		return create_vpx_decoder()

	return None


def create_video_encoder(video_codec : VideoCodec, resolution : Resolution):
	if video_codec == 'av1':
		return create_aom_encoder(resolution, 8000, 8, 10)
	if video_codec == 'vp8':
		return create_vpx_encoder(resolution, 8000, 8, 10)

	return None


def destroy_video_encoder(video_codec : VideoCodec, video_encoder) -> None:
	if video_codec == 'av1':
		destroy_aom_encoder(video_encoder)
	if video_codec == 'vp8':
		destroy_vpx_encoder(video_encoder)


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	yuv_frame = None

	if video_codec == 'av1':
		yuv_frame = decode_aom_buffer(video_decoder, frame_buffer)
	if video_codec == 'vp8':
		yuv_frame = decode_vpx_buffer(video_decoder, frame_buffer)

	if yuv_frame is not None and yuv_frame.shape[1] % 2 == 0 and yuv_frame.shape[0] % 3 == 0:
		return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

	return None


def receive_audio_frame(datachannel_library : ctypes.CDLL, audio_track : int, audio_decoder : OpusDecoder, receive_buffer : ctypes.Array) -> AudioFrame:
	buf_size = ctypes.c_int(8 * 1024)
	result = datachannel_library.rtcReceiveMessage(audio_track, receive_buffer, ctypes.byref(buf_size))

	if result == 0 and buf_size.value > 0:
		opus_buffer = receive_buffer.raw[:buf_size.value]
		decoded_frame = decode_opus_buffer(audio_decoder, opus_buffer, 960, 2)

		if decoded_frame is not None:
			return decoded_frame

	return create_empty_audio_frame()


def poll_for_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array, timeout : float) -> Optional[VisionFrame]:
	deadline = time.monotonic() + timeout

	while time.monotonic() < deadline:
		frame = try_receive_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer)

		if frame is not None:
			return frame

		time.sleep(0.005)

	return None


def try_receive_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array) -> Optional[VisionFrame]:
	buf_size = ctypes.c_int(512 * 1024)
	result = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buf_size))

	if result == 0 and buf_size.value > 0:
		frame_buffer = receive_buffer.raw[:buf_size.value]
		return decode_video_frame(video_codec, video_decoder, frame_buffer)

	return None


def drain_to_latest_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array) -> Optional[VisionFrame]:
	latest_frame = None
	buf_size = ctypes.c_int(512 * 1024)

	while True:
		buf_size.value = 512 * 1024
		result = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buf_size))

		if result != 0 or buf_size.value <= 0:
			break

		frame_buffer = receive_buffer.raw[:buf_size.value]
		decoded = decode_video_frame(video_codec, video_decoder, frame_buffer)

		if decoded is not None:
			latest_frame = decoded

	return latest_frame
