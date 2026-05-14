import ctypes
from typing import Optional

from facefusion.libraries import opus as opus_module
from facefusion.types import OpusEncoder


def create_opus_encoder(sample_rate : int, channel_total : int) -> Optional[OpusEncoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_encoder_create(sample_rate, channel_total, 2049, ctypes.byref(ctypes.c_int(0)))

	return None


def encode_opus_buffer(opus_encoder : OpusEncoder, input_buffer : bytes, frame_size : int) -> bytes:
	opus_library = opus_module.create_static_library()
	output_buffer = b''

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
