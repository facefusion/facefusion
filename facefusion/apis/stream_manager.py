import asyncio
import ctypes
import threading
from collections import deque
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import rtc, rtc_store, streamer
from facefusion.apis.audio_stream import receive_audio_frames
from facefusion.apis.image_stream import receive_vision_frames
from facefusion.apis.video_stream import create_video_encoder, destroy_video_encoder, encode_video_frame, receive_video_frames, update_video_encoder_bitrate
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import opus_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, AudioPack, BitRate, PeerConnection, Resolution, RtcPeer, RtcPeerAudio, SdpAnswer, SdpOffer, SessionId, VideoCodec, VideoPack


async def process_image(websocket : WebSocket) -> None:
	capture_vision_frame = await anext(receive_vision_frames(websocket), None)

	if numpy.any(capture_vision_frame):
		output_vision_frame = streamer.process_frame(create_empty_audio_frame(), capture_vision_frame)
		is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

		if is_success:
			await websocket.send_bytes(output_frame_buffer.tobytes())


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


def destroy_stream(session_id : SessionId) -> bool:
	if rtc_store.has_peers(session_id):
		rtc_store.delete_peers(session_id)
		return not rtc_store.has_peers(session_id)

	return False
