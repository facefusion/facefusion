import ctypes
import threading
import time
from collections import deque
from typing import Optional

import numpy

from facefusion import rtc
from facefusion.apis.stream_event import create_event
from facefusion.codecs import opus_decoder, opus_encoder
from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioCodec, AudioPack, OpusDecoder, RtcPeer, RtcPeerAudio


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
