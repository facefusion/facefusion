import ctypes
from typing import Optional, Tuple

import numpy

from facefusion import rtc_store
from facefusion.libraries import opus as opus_module
from facefusion.types import SessionId


def create_opus_encoder(sample_rate : int, channels : int) -> Optional[ctypes.c_void_p]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		error = ctypes.c_int(0)
		encoder = opus_library.opus_encoder_create(sample_rate, channels, 2049, ctypes.byref(error))

		if error.value == 0:
			return encoder

	return None


def encode_opus(opus_encoder : ctypes.c_void_p, pcm_pointer : ctypes.c_void_p, frame_size : int) -> bytes:
	opus_library = opus_module.create_static_library()
	audio_buffer = b''

	if opus_library:
		output_buffer = ctypes.create_string_buffer(4000)
		encoded_length = opus_library.opus_encode_float(opus_encoder, pcm_pointer, frame_size, output_buffer, 4000)

		if encoded_length > 0:
			audio_buffer = output_buffer.raw[:encoded_length]

	return audio_buffer


def destroy_opus_encoder(opus_encoder : ctypes.c_void_p) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_encoder_destroy(opus_encoder)


def encode_audio_chunk(opus_encoder : ctypes.c_void_p, session_id : SessionId, pcm_data : numpy.ndarray, audio_remainder : numpy.ndarray, audio_timestamp : int) -> Tuple[numpy.ndarray, int]:
	pcm_buffer = numpy.concatenate([ audio_remainder, pcm_data ])
	frame_samples = 1920

	while len(pcm_buffer) >= frame_samples:
		chunk = pcm_buffer[:frame_samples]
		pcm_buffer = pcm_buffer[frame_samples:]
		pcm_pointer = chunk.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
		audio_buffer = encode_opus(opus_encoder, pcm_pointer, 960)

		if audio_buffer:
			rtc_store.send_rtc_audio(session_id, audio_buffer, audio_timestamp)

		audio_timestamp += 960

	return pcm_buffer, audio_timestamp
