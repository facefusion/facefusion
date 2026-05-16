import ctypes
from typing import Optional

import numpy

from facefusion.libraries import opus as opus_module
from facefusion.types import AudioFrame, OpusDecoder, OpusEncoder


def create_opus_encoder(sample_rate : int, channel_total : int) -> Optional[OpusEncoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_encoder_create(sample_rate, channel_total, 2049, ctypes.byref(ctypes.c_int(0)))

	return None


def encode_opus_buffer(opus_encoder : OpusEncoder, input_buffer : bytes, frame_size : int) -> bytes:
	opus_library = opus_module.create_static_library()
	output_buffer = bytes()

	if opus_library:
		temp_buffer = ctypes.create_string_buffer(2048)
		encode_buffer = ctypes.cast(ctypes.create_string_buffer(input_buffer), ctypes.POINTER(ctypes.c_float))
		encode_length = opus_library.opus_encode_float(opus_encoder, encode_buffer, frame_size, temp_buffer, 2048)

		if encode_length:
			output_buffer = temp_buffer.raw[:encode_length]

	return output_buffer


def destroy_opus_encoder(opus_encoder : OpusEncoder) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_encoder_destroy(opus_encoder)


#TODO: needs review
def create_opus_decoder(sample_rate : int, channel_total : int) -> Optional[OpusDecoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_decoder_create(sample_rate, channel_total, ctypes.byref(ctypes.c_int(0)))

	return None


#TODO: needs review
def decode_opus_buffer(opus_decoder : OpusDecoder, input_buffer : bytes, frame_size : int, channel_total : int) -> Optional[AudioFrame]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		decode_buffer = (ctypes.c_float * (frame_size * channel_total))()
		decode_length = opus_library.opus_decode_float(opus_decoder, input_buffer, len(input_buffer), decode_buffer, frame_size, 0)

		if decode_length > 0:
			return numpy.ctypeslib.as_array(decode_buffer, shape = (decode_length * channel_total,)).copy()

	return None


#TODO: needs review
def destroy_opus_decoder(opus_decoder : OpusDecoder) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_decoder_destroy(opus_decoder)
