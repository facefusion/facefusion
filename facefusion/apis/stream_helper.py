import contextlib
import ctypes
import queue
import threading
import time
from collections.abc import AsyncIterator
from typing import Optional

import cv2
import numpy
from starlette.websockets import WebSocket

from facefusion import rtc, rtc_store, state_manager, streamer
from facefusion.audio import create_empty_audio_frame
from facefusion.codecs import aom_decoder, aom_encoder, opus_decoder, opus_encoder, vpx_decoder, vpx_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AomDecoder, AomEncoder, AudioCodec, AudioFrame, PeerConnection, Resolution, RtcPeer, SdpAnswer, SdpOffer, SessionId, VideoCodec, VisionFrame, VpxDecoder, VpxEncoder


async def process_image(websocket : WebSocket) -> None:
	source_paths = state_manager.get_item('source_paths')

	if source_paths:
		capture_vision_frame = await anext(receive_vision_frames(websocket), None)

		if numpy.any(capture_vision_frame):
			output_vision_frame = streamer.process_frame(create_empty_audio_frame(), capture_vision_frame)
			is_success, output_frame_buffer = cv2.imencode('.jpg', output_vision_frame)

			if is_success:
				await websocket.send_bytes(output_frame_buffer.tobytes())


#TODO: needs review
def process_video(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	video_codec : VideoCodec = 'vp8'
	av1_payload_type = rtc.get_payload_type(sdp_offer, 'av1')

	if av1_payload_type:
		video_codec = 'av1'

	video_payload_type = rtc.get_payload_type(sdp_offer, video_codec)

	if video_payload_type:
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

			threading.Thread(target = run_peer_loop, args = (session_id, rtc_peer), daemon = True).start()

		return local_sdp

	return None


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
	video_codec = rtc_peer.get('video').get('codec')
	video_track = rtc_peer.get('video').get('receiver_track')
	video_queue : queue.Queue[VisionFrame] = queue.Queue(maxsize = 1)
	audio_queue : queue.Queue[AudioFrame] = queue.Queue(maxsize = 4)
	receiver_threads = [threading.Thread(target = receive_video_frames, args = (video_track, video_codec, video_queue), daemon = True)]

	if rtc_peer.get('audio'):
		audio_track = rtc_peer.get('audio').get('receiver_track')
		receiver_threads.append(threading.Thread(target = receive_audio_frames, args = (audio_track, audio_queue), daemon = True))

	for receiver_thread in receiver_threads:
		receiver_thread.start()

	temp_vision_frame = video_queue.get()

	if numpy.any(temp_vision_frame):
		audio_frame = create_empty_audio_frame()
		temp_resolution : Resolution = (temp_vision_frame.shape[1], temp_vision_frame.shape[0])
		video_encoder = create_video_encoder(video_codec, temp_resolution)
		audio_encoder = opus_encoder.create(48000, 2)
		frame_index = 0

		while numpy.any(temp_vision_frame):
			with contextlib.suppress(queue.Empty):
				audio_frame = audio_queue.get_nowait()

			output_vision_frame = streamer.process_frame(audio_frame, temp_vision_frame)
			output_resolution : Resolution = (output_vision_frame.shape[1], output_vision_frame.shape[0])
			output_vision_buffer = cv2.cvtColor(output_vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

			if output_resolution == temp_resolution:
				output_video_buffer = encode_video_frame(video_codec, video_encoder, output_vision_buffer, temp_resolution, frame_index)
			else:
				destroy_video_encoder(video_codec, video_encoder)
				temp_resolution = output_resolution
				video_encoder = create_video_encoder(video_codec, temp_resolution)
				output_video_buffer = encode_video_frame(video_codec, video_encoder, output_vision_buffer, temp_resolution, frame_index)

			send_timestamp = time.monotonic()

			if output_video_buffer:
				rtc.send_video(rtc_peer, output_video_buffer, int(send_timestamp * 90000))

			if audio_encoder and audio_frame.dtype == numpy.float32:
				output_audio_buffer = opus_encoder.encode(audio_encoder, audio_frame.tobytes(), 960)

				if output_audio_buffer:
					rtc.send_audio(rtc_peer, output_audio_buffer, int(send_timestamp * 48000))

			frame_index += 1
			temp_vision_frame = video_queue.get()

		destroy_video_encoder(video_codec, video_encoder)
		opus_encoder.destroy(audio_encoder)

	for receiver_thread in receiver_threads:
		receiver_thread.join()

	rtc_store.delete_peers(session_id)


def receive_video_frames(video_track : int, video_codec : VideoCodec, video_queue : queue.Queue[VisionFrame]) -> None:
	datachannel_library = datachannel_module.create_static_library()
	video_decoder = create_video_decoder(video_codec)
	receive_buffer = ctypes.create_string_buffer(512 * 1024)
	receive_status_code = -3

	while receive_status_code == 0 or receive_status_code == -3:
		buffer_size = ctypes.c_int(512 * 1024)
		receive_status_code = datachannel_library.rtcReceiveMessage(video_track, receive_buffer, ctypes.byref(buffer_size))

		if receive_status_code == 0 and buffer_size.value > 0:
			frame_buffer = receive_buffer.raw[:buffer_size.value]
			vision_frame = decode_video_frame(video_codec, video_decoder, frame_buffer)

			if numpy.any(vision_frame):
				with contextlib.suppress(queue.Empty):
					video_queue.get_nowait()
				video_queue.put_nowait(vision_frame)

		if receive_status_code == -3:
			time.sleep(0.001)  # TODO: remove sleep

	video_queue.put(numpy.empty(0))

	if video_codec == 'av1':
		aom_decoder.destroy(video_decoder)
	if video_codec == 'vp8':
		vpx_decoder.destroy(video_decoder)


def receive_audio_frames(audio_track : int, audio_queue : queue.Queue[AudioFrame]) -> None:
	datachannel_library = datachannel_module.create_static_library()
	audio_decoder = opus_decoder.create(48000, 2)
	receive_buffer = ctypes.create_string_buffer(8 * 1024)
	receive_status_code = -3

	while receive_status_code == 0 or receive_status_code == -3:
		buffer_size = ctypes.c_int(8 * 1024)
		receive_status_code = datachannel_library.rtcReceiveMessage(audio_track, receive_buffer, ctypes.byref(buffer_size))

		if receive_status_code == 0 and buffer_size.value > 0:
			opus_buffer = receive_buffer.raw[:buffer_size.value]
			output_buffer = opus_decoder.decode(audio_decoder, opus_buffer, 960, 2)

			if output_buffer:
				audio_queue.put(numpy.frombuffer(output_buffer, dtype = numpy.float32))

		if receive_status_code == -3:
			time.sleep(0.001) # TODO: remove sleep

	opus_decoder.destroy(audio_decoder)


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


def destroy_stream(session_id : SessionId) -> bool:
	if rtc_store.get_peers(session_id):
		rtc_store.delete_peers(session_id)
		return True

	return False


def decode_video_frame(video_codec : VideoCodec, video_decoder : VpxDecoder | AomDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	if video_codec == 'av1':
		aom_pointer = aom_decoder.decode(video_decoder, frame_buffer)

		if aom_pointer:
			frame_width, frame_height = aom_pointer.get('resolution')
			vision_frame = numpy.frombuffer(aom_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
			return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)

	if video_codec == 'vp8':
		vpx_pointer = vpx_decoder.decode(video_decoder, frame_buffer)

		if vpx_pointer:
			frame_width, frame_height = vpx_pointer.get('resolution')
			vision_frame = numpy.frombuffer(vpx_pointer.get('buffer'), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
			return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)

	return None


def encode_video_frame(video_codec : VideoCodec, video_encoder : VpxEncoder | AomEncoder, raw_frame_bytes : bytes, resolution : Resolution, frame_index : int) -> bytes:
	if video_codec == 'av1':
		return aom_encoder.encode(video_encoder, raw_frame_bytes, resolution, frame_index)

	if video_codec == 'vp8':
		return vpx_encoder.encode(video_encoder, raw_frame_bytes, resolution, frame_index)

	return bytes()
