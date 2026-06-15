import ctypes
import time
from functools import partial
from queue import Queue
from typing import Optional, Tuple

import numpy

from facefusion import rtc
from facefusion.apis.stream_event import create_receive_event
from facefusion.codecs import opus_decoder, opus_encoder
from facefusion.types import AudioCodec, AudioFrame, OpusDecoder, RtcPeer, RtcPeerAudio


def run_audio_encode_loop(rtc_peer : RtcPeer, audio_queue : Queue[Tuple[float, AudioFrame]]) -> None:
	temp_audio_time, temp_audio_frame = audio_queue.get()
	audio_encoder = opus_encoder.create(48000, 2)
	audio_timestamp = 0

	while numpy.any(temp_audio_frame):
		audio_frame_size = len(temp_audio_frame) // 2
		audio_buffer = opus_encoder.encode(audio_encoder, temp_audio_frame.tobytes(), audio_frame_size)

		if audio_buffer:
			rtc.send_audio(rtc_peer, audio_buffer, audio_timestamp)
			audio_timestamp += audio_frame_size

		temp_audio_time, temp_audio_frame = audio_queue.get()

	opus_encoder.destroy(audio_encoder)


def receive_audio_frames(rtc_peer_audio : RtcPeerAudio, audio_queue : Queue[Tuple[float, AudioFrame]]) -> None:
	audio_track = rtc_peer_audio.get('receiver_track')
	audio_codec = rtc_peer_audio.get('codec')
	audio_decoder = create_audio_decoder(audio_codec)

	audio_frame_handler = partial(handle_audio_frame, audio_codec, audio_decoder, audio_queue)
	receive_event = create_receive_event(audio_track, audio_frame_handler)
	receive_event.wait()

	empty_audio_frame = numpy.empty(0)
	audio_queue.put((0.0, empty_audio_frame))
	destroy_audio_decoder(audio_codec, audio_decoder)


def decode_audio_frame(audio_codec : AudioCodec, audio_decoder : OpusDecoder, input_buffer : bytes) -> Optional[bytes]:
	if audio_codec == 'opus':
		return opus_decoder.decode(audio_decoder, input_buffer, 960, 2)
	return None


def create_audio_decoder(audio_codec : AudioCodec) -> Optional[OpusDecoder]:
	if audio_codec == 'opus':
		return opus_decoder.create(48000, 2)
	return None


def destroy_audio_decoder(audio_codec : AudioCodec, audio_decoder : OpusDecoder) -> None:
	if audio_codec == 'opus':
		opus_decoder.destroy(audio_decoder)


#todo: Alias Time for float
def handle_audio_frame(audio_codec : AudioCodec, audio_decoder : OpusDecoder, audio_queue : Queue[Tuple[float, AudioFrame]], track : int, data : ctypes.c_void_p, size : int, info : ctypes.c_void_p, pointer : ctypes.c_void_p) -> None:
	audio_buffer = ctypes.string_at(data, size)
	audio_frame = decode_audio_frame(audio_codec, audio_decoder, audio_buffer)

	if audio_frame:
		temp_audio_frame = numpy.frombuffer(audio_frame, dtype = numpy.float32)
		audio_queue.put((time.monotonic(), temp_audio_frame))
