import asyncio
import ctypes
import time
from collections.abc import AsyncIterator
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc, rtc_store, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.codecs.aom import create_aom_decoder, create_aom_encoder, decode_aom_buffer, destroy_aom_decoder, destroy_aom_encoder, encode_aom_buffer
from facefusion.codecs.vpx import create_vpx_decoder, create_vpx_encoder, decode_vpx_buffer, destroy_vpx_decoder, destroy_vpx_encoder, encode_vpx_buffer
from facefusion.libraries import datachannel as datachannel_module
from facefusion.streamer import process_vision_frame
from facefusion.types import AomDecoder, PeerConnection, Resolution, RtcAudioTrack, RtcPeer, RtcVideoTrack, SdpAnswer, SdpOffer, SessionId, VideoCodec, VisionFrame, VpxDecoder

RTC_STATE_NAMES = [ 'new', 'connecting', 'connected', 'disconnected', 'failed', 'closed' ]
peer_connection_labels : dict = {}
WHIP_SESSIONS : dict = {}


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
			output_vision_frame = process_vision_frame(capture_vision_frame)
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


def receive_video(session_id : SessionId, sdp_offer : SdpOffer, codec : str) -> Optional[SdpAnswer]:
	datachannel_library = datachannel_module.create_static_library()
	rtc_store.init_peers(session_id)
	sdp_media = rtc.detect_sdp_media(sdp_offer)
	peer_connection : PeerConnection = rtc.create_peer_connection()
	register_state_change_callback(peer_connection, 'whip')

	video_media = sdp_media.get('video')

	if not video_media:
		return None

	video_codec = video_media.get('codec')
	payload_type = video_media.get('payload_type')
	video_track = add_receive_track(peer_connection, video_codec, payload_type)

	video_decoder = create_video_decoder(video_codec)

	WHIP_SESSIONS[session_id] =\
	{
		'peer_connection': peer_connection,
		'video_track': video_track,
		'video_decoder': video_decoder,
		'video_codec': video_codec,
		'codec': codec,
		'active': True
	}

	rtc.set_remote_description(peer_connection, sdp_offer)
	local_sdp = rtc.create_sdp_answer(peer_connection)

	if local_sdp:
		event_loop = asyncio.get_event_loop()
		event_loop.run_in_executor(None, run_whip_loop, session_id, codec)

	return local_sdp


def send_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	rtc_peers = rtc_store.get_peers(session_id)

	if rtc_peers is not None:
		sdp_media = rtc.detect_sdp_media(sdp_offer)
		peer_connection : PeerConnection = rtc.create_peer_connection()
		register_state_change_callback(peer_connection, 'whep')
		rtc.set_remote_description(peer_connection, sdp_offer)

		audio_track : RtcAudioTrack = rtc.add_audio_track(peer_connection, 'sendonly', sdp_media.get('audio').get('codec'), sdp_media.get('audio').get('payload_type'))
		video_track : RtcVideoTrack = rtc.add_video_track(peer_connection, 'sendonly', sdp_media.get('video').get('codec'), sdp_media.get('video').get('payload_type'))
		local_sdp = rtc.create_sdp_answer(peer_connection)

		if local_sdp:
			rtc_peer : RtcPeer =\
			{
				'peer_connection': peer_connection,
				'video_track': video_track,
				'audio_track': audio_track
			}
			rtc_peers.append(rtc_peer)

		return local_sdp

	return None


def disconnect_whip(session_id : SessionId) -> None:
	whip_session = WHIP_SESSIONS.get(session_id)

	if whip_session:
		whip_session['active'] = False

		video_decoder = whip_session.get('video_decoder')
		video_codec = whip_session.get('video_codec')

		if video_decoder:
			if video_codec == 'av1':
				destroy_aom_decoder(video_decoder)
			if video_codec == 'vp8':
				destroy_vpx_decoder(video_decoder)

		datachannel_library = datachannel_module.create_static_library()
		peer_connection = whip_session.get('peer_connection')

		if peer_connection:
			datachannel_library.rtcDeletePeerConnection(peer_connection)

		del WHIP_SESSIONS[session_id]

	rtc_store.delete_peers(session_id)


def run_whip_loop(session_id : SessionId, codec : str) -> None:
	whip_session = WHIP_SESSIONS.get(session_id)

	if not whip_session:
		return

	datachannel_library = datachannel_module.create_static_library()
	video_track = whip_session.get('video_track')
	video_decoder = whip_session.get('video_decoder')
	video_codec = whip_session.get('video_codec')
	receive_buffer = ctypes.create_string_buffer(512 * 1024)

	vision_frame = poll_for_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer, 30.0)

	if vision_frame is None:
		return

	resolution : Resolution = (vision_frame.shape[1], vision_frame.shape[0])

	if codec == 'av1':
		encoder = create_aom_encoder(resolution, 8000, 8, 10)
	if codec == 'vp8':
		encoder = create_vpx_encoder(resolution, 8000, 8, 10)

	frame_index = 0

	while whip_session.get('active'):
		rtc_peers = rtc_store.get_peers(session_id)

		if not rtc_peers or not has_open_peer(rtc_peers):
			time.sleep(0.01)
			next_frame = poll_for_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer, 5.0)

			if next_frame is None:
				break
			vision_frame = next_frame
			continue

		output_vision_frame = process_vision_frame(vision_frame)
		output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])

		if output_resolution != resolution:
			resolution = output_resolution

			if codec == 'av1':
				destroy_aom_encoder(encoder)
				encoder = create_aom_encoder(resolution, 8000, 8, 10)
			if codec == 'vp8':
				destroy_vpx_encoder(encoder)
				encoder = create_vpx_encoder(resolution, 8000, 8, 10)

		yuv_frame = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420)

		if codec == 'av1':
			encoded_buffer = encode_aom_buffer(encoder, yuv_frame.tobytes(), resolution, frame_index)
		if codec == 'vp8':
			encoded_buffer = encode_vpx_buffer(encoder, yuv_frame.tobytes(), resolution, frame_index)

		if encoded_buffer:
			timestamp = int(time.monotonic() * 90000)
			rtc.send_video_to_peers(rtc_peers, encoded_buffer, timestamp)

		frame_index += 1

		next_frame = drain_to_latest_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer)

		if next_frame is not None:
			vision_frame = next_frame
			continue

		next_frame = poll_for_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer, 30.0)

		if next_frame is None:
			break

		vision_frame = next_frame

	if codec == 'av1':
		destroy_aom_encoder(encoder)
	if codec == 'vp8':
		destroy_vpx_encoder(encoder)


def add_receive_track(peer_connection : PeerConnection, video_codec : VideoCodec, payload_type : int) -> int:
	datachannel_library = datachannel_module.create_static_library()
	track_init = datachannel_module.define_rtc_track_init()
	track_init.direction = 2
	track_init.payloadType = payload_type
	track_init.ssrc = 42
	track_init.name = b'video'
	track_init.mid = b'0'

	if video_codec == 'av1':
		track_init.codec = 4
	if video_codec == 'vp8':
		track_init.codec = 1

	video_track = datachannel_library.rtcAddTrackEx(peer_connection, ctypes.byref(track_init))

	if video_codec == 'av1':
		datachannel_library.rtcSetAV1Depacketizer(video_track, 1)
	if video_codec == 'vp8':
		depacketizer_init = datachannel_module.define_rtc_packetizer_init()
		depacketizer_init.ssrc = 0
		depacketizer_init.cname = b'video'
		depacketizer_init.payloadType = payload_type
		depacketizer_init.clockRate = 90000
		datachannel_library.rtcSetVP8Depacketizer(video_track, ctypes.byref(depacketizer_init))

	datachannel_library.rtcChainRtcpReceivingSession(video_track)

	return video_track


def create_video_decoder(video_codec : str) -> Optional[VpxDecoder | AomDecoder]:
	if video_codec == 'av1':
		return create_aom_decoder()
	if video_codec == 'vp8':
		return create_vpx_decoder()
	return None


def decode_whip_frame(video_codec : str, video_decoder : VpxDecoder | AomDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	yuv_frame = None

	if video_codec == 'av1':
		yuv_frame = decode_aom_buffer(video_decoder, frame_buffer)
	if video_codec == 'vp8':
		yuv_frame = decode_vpx_buffer(video_decoder, frame_buffer)

	if yuv_frame is not None and yuv_frame.shape[1] % 2 == 0 and yuv_frame.shape[0] % 3 == 0:
		return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

	return None


def has_open_peer(rtc_peers : list) -> bool:
	datachannel_library = datachannel_module.create_static_library()

	for rtc_peer in rtc_peers:
		video_track = rtc_peer.get('video_track')

		if datachannel_library.rtcIsOpen(video_track):
			return True

	return False


def poll_for_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : str, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array, timeout : float) -> Optional[VisionFrame]:
	deadline = time.monotonic() + timeout

	while time.monotonic() < deadline:
		frame = try_receive_frame(datachannel_library, video_track, video_codec, video_decoder, receive_buffer)

		if frame is not None:
			return frame

		time.sleep(0.005)

	return None


def try_receive_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : str, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array) -> Optional[VisionFrame]:
	buf_size = ctypes.c_int(512 * 1024)
	result = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buf_size))

	if result == 0 and buf_size.value > 0:
		frame_buffer = receive_buffer.raw[:buf_size.value]
		return decode_whip_frame(video_codec, video_decoder, frame_buffer)

	return None


def drain_to_latest_frame(datachannel_library : ctypes.CDLL, video_track : int, video_codec : str, video_decoder : VpxDecoder | AomDecoder, receive_buffer : ctypes.Array) -> Optional[VisionFrame]:
	latest_frame = None
	buf_size = ctypes.c_int(512 * 1024)

	while True:
		buf_size.value = 512 * 1024
		result = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buf_size))

		if result != 0 or buf_size.value <= 0:
			break

		frame_buffer = receive_buffer.raw[:buf_size.value]
		decoded = decode_whip_frame(video_codec, video_decoder, frame_buffer)

		if decoded is not None:
			latest_frame = decoded

	return latest_frame


def register_state_change_callback(peer_connection : PeerConnection, label : str) -> None:
	datachannel_library = datachannel_module.create_static_library()
	peer_connection_labels[peer_connection] = label
	datachannel_library.rtcSetStateChangeCallback(peer_connection, STATE_CHANGE_CALLBACK)


def handle_state_change(pc : int, state : int, user_ptr : ctypes.c_void_p) -> None:
	state_name = RTC_STATE_NAMES[state] if state < len(RTC_STATE_NAMES) else str(state)
	label = peer_connection_labels.get(pc, 'unknown')
	print('[' + label + '] peer ' + str(pc) + ' state: ' + state_name, flush = True)


STATE_CHANGE_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)(handle_state_change)
