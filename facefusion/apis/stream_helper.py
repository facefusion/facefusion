import asyncio
import queue # TODO: try deque
import time
from collections.abc import AsyncIterator
from typing import Optional, Tuple, cast, get_args

import cv2
import numpy
from starlette.websockets import WebSocket, WebSocketState

from facefusion import rtc, rtc_store, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.codecs.aom import create_aom_encoder, destroy_aom_encoder, encode_aom_buffer
from facefusion.codecs.opus import create_opus_encoder, destroy_opus_encoder, encode_opus_buffer
from facefusion.codecs.vpx import create_vpx_encoder, destroy_vpx_encoder, encode_vpx_buffer
from facefusion.streamer import process_vision_frame
from facefusion.types import AudioCodec, PeerConnection, Resolution, RtcAudioTrack, RtcPeer, RtcVideoTrack, SdpAnswer, SdpOffer, SessionId, VideoCodec, VisionFrame


# TODO: refine this method
async def handle_video_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)
	session_context.set_session_id(session_id)
	stream_codec : VideoCodec = 'av1'

	if websocket.query_params.get('codec') in get_args(VideoCodec):
		stream_codec = cast(VideoCodec, websocket.query_params.get('codec'))

	await websocket.accept(subprotocol = subprotocol)

	if session_id:
		stream_frames = receive_stream_frames(websocket)
		first_vision_frame : Optional[VisionFrame] = None

		async for first_frame_type, first_frame_buffer in stream_frames:
			if first_frame_type == 1:
				first_vision_frame = cv2.imdecode(numpy.frombuffer(first_frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)
				break

		if numpy.any(first_vision_frame):
			resolution : Resolution = (first_vision_frame.shape[1], first_vision_frame.shape[0])
			vision_frame_queue : queue.Queue[Optional[VisionFrame]] = queue.Queue()
			audio_chunk_queue : queue.Queue[Optional[bytes]] = queue.Queue()
			audio_temp = numpy.array([], dtype = numpy.float32)

			vision_frame_queue.put(first_vision_frame)
			rtc_store.init_peers(session_id)

			event_loop = asyncio.get_running_loop()

			if stream_codec == 'av1':
				video_encode_task = event_loop.run_in_executor(None, run_aom_encode_loop, vision_frame_queue, session_id, resolution)
			if stream_codec == 'vp8':
				video_encode_task = event_loop.run_in_executor(None, run_vp8_encode_loop, vision_frame_queue, session_id, resolution)

			audio_encode_task = event_loop.run_in_executor(None, run_opus_encode_loop, audio_chunk_queue, session_id)
			await websocket.send_text('ready')

			async for frame_type, frame_buffer in stream_frames:
				if frame_type == 1:
					vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

					if numpy.any(vision_frame):
						if vision_frame_queue.qsize():
							vision_frame_queue.get_nowait()
						vision_frame_queue.put(vision_frame)

				if frame_type == 2:
					audio_temp = numpy.concatenate([ audio_temp, numpy.frombuffer(frame_buffer, dtype = numpy.float32) ])

					while len(audio_temp) >= 1920:
						audio_chunk_queue.put(audio_temp[:1920].tobytes())
						audio_temp = audio_temp[1920:]

			vision_frame_queue.put(None)
			audio_chunk_queue.put(None)

			await video_encode_task
			await audio_encode_task

			rtc_store.delete_peers(session_id)

	if websocket.client_state == WebSocketState.CONNECTED:
		await websocket.close()


# TODO: extract shared session setup from handle_image_stream and handle_video_stream, guard session_id like handle_video_stream
async def handle_image_stream(websocket : WebSocket) -> None:
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


# TODO: clean up peer connection on failed sdp negotiation, wrap in run_in_executor to avoid blocking async event loop
def connect_rtc(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	rtc_peers = rtc_store.get_peers(session_id)

	if rtc_peers is not None:
		payload_types = rtc.get_payload_types(sdp_offer)
		peer_connection : PeerConnection = rtc.create_peer_connection()
		rtc.set_remote_description(peer_connection, sdp_offer)

		audio_codec : AudioCodec = 'opus'
		audio_track : RtcAudioTrack = rtc.add_audio_track(peer_connection, 'sendonly', audio_codec, payload_types.get(audio_codec, 111))

		#TODO: Fix me via resolve method
		video_codec : VideoCodec = 'av1'
		if payload_types.get('av1'):
			video_codec = 'av1'
		if payload_types.get('vp8'):
			video_codec = 'vp8'

		video_track : RtcVideoTrack = rtc.add_video_track(peer_connection, 'sendonly', video_codec, payload_types.get(video_codec, 96))
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


# TODO: switch to loop_encode_video or encode_video_loop ... pass video_codec to follow standards
def run_aom_encode_loop(vision_frame_queue : queue.Queue[Optional[VisionFrame]], session_id : SessionId, frame_resolution : Resolution) -> None:
	aom_encoder = create_aom_encoder(frame_resolution, 4500, 8, 10)
	temp_resolution = frame_resolution
	timestamp = 0

	vision_frame = vision_frame_queue.get()

	while numpy.any(vision_frame) and aom_encoder:
		output_vision_frame = process_vision_frame(vision_frame)
		output_resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])

		if output_resolution == temp_resolution:
			output_frame_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
			output_frame_buffer = encode_aom_buffer(aom_encoder, output_frame_buffer, output_resolution, timestamp)
			rtc_peers = rtc_store.get_peers(session_id)

			if output_frame_buffer and rtc_peers:
				video_timestamp = int(time.monotonic() * 90000)
				rtc.send_video_to_peers(rtc_peers, output_frame_buffer, video_timestamp)

			timestamp += 1
			vision_frame = vision_frame_queue.get()
			#TODO: we are not using continue as control flow in the project
			continue

		destroy_aom_encoder(aom_encoder)
		temp_resolution = output_resolution
		aom_encoder = create_aom_encoder(temp_resolution, 4500, 8, 10)
		timestamp = 0

	if aom_encoder:
		destroy_aom_encoder(aom_encoder)


# TODO: switch to loop_encode_video or encode_video_loop ... pass video_codec to follow standards
def run_vp8_encode_loop(vision_frame_queue : queue.Queue[Optional[VisionFrame]], session_id : SessionId, frame_resolution : Resolution) -> None:
	vpx_encoder = create_vpx_encoder(frame_resolution, 4500, 8, 16)
	temp_resolution = frame_resolution
	timestamp = 0

	vision_frame = vision_frame_queue.get()

	while numpy.any(vision_frame) and vpx_encoder:
		output_vision_frame = process_vision_frame(vision_frame)
		output_resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])

		if output_resolution == temp_resolution:
			output_frame_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
			output_frame_buffer = encode_vpx_buffer(vpx_encoder, output_frame_buffer, output_resolution, timestamp)
			rtc_peers = rtc_store.get_peers(session_id)

			if output_frame_buffer and rtc_peers:
				video_timestamp = int(time.monotonic() * 90000)
				rtc.send_video_to_peers(rtc_peers, output_frame_buffer, video_timestamp)

			timestamp += 1
			vision_frame = vision_frame_queue.get()
			# TODO: we are not using continue as control flow in the project
			continue

		destroy_vpx_encoder(vpx_encoder)
		temp_resolution = output_resolution
		vpx_encoder = create_vpx_encoder(temp_resolution, 4500, 8, 16)
		timestamp = 0

	if vpx_encoder:
		destroy_vpx_encoder(vpx_encoder)


# TODO: switch to loop_encode_audio or encode_audio_loop ... pass audio_codec to follow standards
def run_opus_encode_loop(audio_chunk_queue : queue.Queue[Optional[bytes]], session_id : SessionId) -> None:
	opus_encoder = create_opus_encoder(48000, 2)
	audio_timestamp = 0

	audio_chunk = audio_chunk_queue.get()

	while audio_chunk: # TODO: improve this condition with b''
		audio_buffer = encode_opus_buffer(opus_encoder, audio_chunk, 960)
		rtc_peers = rtc_store.get_peers(session_id)

		if audio_buffer and rtc_peers:
			rtc.send_audio_to_peers(rtc_peers, audio_buffer, audio_timestamp)

		audio_timestamp += 960
		audio_chunk = audio_chunk_queue.get()

	if opus_encoder:
		destroy_opus_encoder(opus_encoder)


# TODO: needs refinement
async def receive_stream_frames(websocket : WebSocket) -> AsyncIterator[Tuple[int, bytes]]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()

		if len(frame_buffer) > 1:
			yield frame_buffer[0], frame_buffer[1:]

		websocket_event = await websocket.receive()


# TODO: needs refinement, does it receive frames or a buffer?
async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()
