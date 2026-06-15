import ctypes
from typing import Optional

from facefusion.libraries import opus as opus_module
from facefusion.types import Buffer, OpusEncoder


def create(sample_rate : int, channel_total : int) -> Optional[OpusEncoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_encoder_create(sample_rate, channel_total, 2049, ctypes.byref(ctypes.c_int(0)))

	return None


def encode(opus_encoder : OpusEncoder, input_buffer : Buffer, channel_total : int) -> Buffer:
	opus_library = opus_module.create_static_library()
	output_buffer = bytes()

	if opus_library:
		sample_size = ctypes.sizeof(ctypes.c_float)
		sample_total = len(input_buffer) // (sample_size * channel_total)
		sample_buffer = (ctypes.c_float * (sample_total * channel_total)).from_buffer_copy(input_buffer)
		temp_buffer = ctypes.create_string_buffer(2048)
		output_total = opus_library.opus_encode_float(opus_encoder, sample_buffer, sample_total, temp_buffer, 2048)

		if output_total:
			output_buffer = temp_buffer.raw[:output_total]

	return output_buffer


def destroy(opus_encoder : OpusEncoder) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_encoder_destroy(opus_encoder)
