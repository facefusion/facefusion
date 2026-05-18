import ctypes
from typing import Optional

from facefusion.libraries import opus as opus_module
from facefusion.types import OpusDecoder


def create_opus_decoder(sample_rate : int, channel_total : int) -> Optional[OpusDecoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_decoder_create(sample_rate, channel_total, ctypes.byref(ctypes.c_int(0)))

	return None


def decode(opus_decoder : OpusDecoder, input_buffer : bytes, frame_size : int, channel_total : int) -> bytes:
	opus_library = opus_module.create_static_library()
	output_buffer = bytes()

	if opus_library:
		input_total = len(input_buffer)
		decode_buffer = (ctypes.c_float * (frame_size * channel_total))()
		decode_length = opus_library.opus_decode_float(opus_decoder, input_buffer, input_total, decode_buffer, frame_size, 0)

		if decode_length:
			output_buffer = ctypes.string_at(ctypes.addressof(decode_buffer), decode_length * channel_total * ctypes.sizeof(ctypes.c_float))

	return output_buffer


def destroy_opus_decoder(opus_decoder : OpusDecoder) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_decoder_destroy(opus_decoder)
