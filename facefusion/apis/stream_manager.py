import ctypes
import threading
from collections.abc import AsyncIterator
from queue import Queue
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import rtc, rtc_store, streamer
from facefusion.apis.stream_audio import receive_audio_frames, run_audio_encode_loop
from facefusion.apis.stream_video import receive_video_frames, run_video_encode_loop
from facefusion.audio import create_empty_audio_frame
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, AudioPack, PeerConnection, RtcPeer, RtcPeerAudio, SdpAnswer, SdpOffer, SessionId, VideoCodec, VideoPack, VisionFrame


async def process_image(websocket : WebSocket) -> None:
	capture_vision_frame = await anext(receive_vision_frames(websocket), None)

	if numpy.any(capture_vision_frame):
		output_vision_frame = streamer.process_frame(create_empty_audio_frame(), capture_vision_frame)
		is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

		if is_success:
			await websocket.send_bytes(output_frame_buffer.tobytes())


async def receive_vision_frames(websocket : WebSocket) -> AsyncIterator[VisionFrame]:
	websocket_event = await websocket.receive()

	while websocket_event.get('type') == 'websocket.receive':
		frame_buffer = websocket_event.get('bytes') or bytes()
		vision_frame = cv2.imdecode(numpy.frombuffer(frame_buffer, numpy.uint8), cv2.IMREAD_COLOR)

		if numpy.any(vision_frame):
			yield vision_frame

		websocket_event = await websocket.receive()


def process_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	video_codec : VideoCodec = 'vp8'

	if rtc.get_payload_type(sdp_offer, 'vp9'):
		video_codec = 'vp9'

	if rtc.get_payload_type(sdp_offer, 'av1'):
		video_codec = 'av1'

	video_payload_type = rtc.get_payload_type(sdp_offer, video_codec)

	if video_payload_type:
		peer_connection : PeerConnection = rtc.create_peer_connection()
		video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', video_codec, video_payload_type)
		video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', video_codec, video_payload_type)

		sender_bitrate = ctypes.c_uint(0)
		receiver_bitrate = ctypes.c_uint(8000)
		rtc.wire_sender_bitrate(video_sender_track, sender_bitrate)

		audio_codec : AudioCodec = 'opus'
		audio_payload_type = rtc.get_payload_type(sdp_offer, audio_codec)

		if audio_payload_type:
			audio_receiver_track = rtc.add_audio_track(peer_connection, 'recvonly', audio_codec, audio_payload_type)
			audio_sender_track = rtc.add_audio_track(peer_connection, 'sendonly', audio_codec, audio_payload_type)

		rtc.set_remote_description(peer_connection, sdp_offer)
		sdp_answer = rtc.create_sdp_answer(peer_connection)

		if sdp_answer:
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

			threading.Thread(target = run_peer_loop, args = (session_id, rtc_peer), daemon = True).start()

			return sdp_answer

		datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection)

	return None


def run_peer_loop(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	video_queue : Queue[VideoPack] = Queue(maxsize = 30)
	audio_queue : Queue[AudioPack] = Queue(maxsize = 300)

	video_receiver_thread = threading.Thread(target = receive_video_frames, args = (rtc_peer.get('video'), video_queue), daemon = True)
	video_encoder_thread = threading.Thread(target = run_video_encode_loop, args = (rtc_peer, video_queue), daemon = True)
	video_receiver_thread.start()
	video_encoder_thread.start()

	if rtc_peer.get('audio'):
		audio_receiver_thread = threading.Thread(target = receive_audio_frames, args = (rtc_peer.get('audio'), audio_queue), daemon = True)
		audio_encoder_thread = threading.Thread(target = run_audio_encode_loop, args = (rtc_peer, audio_queue), daemon = True)
		audio_receiver_thread.start()
		audio_encoder_thread.start()
		audio_receiver_thread.join()
		audio_encoder_thread.join()

	video_receiver_thread.join()
	video_encoder_thread.join()
	rtc_store.delete_peers(session_id)


def destroy_stream(session_id : SessionId) -> bool:
	if rtc_store.has_peers(session_id):
		rtc_store.delete_peers(session_id)
		return not rtc_store.has_peers(session_id)

	return False
