import ctypes
from typing import Optional

from facefusion.libraries import opus as opus_module
from facefusion.types import Buffer, OpusDecoder


def create(sample_rate : int, channel_total : int) -> Optional[OpusDecoder]:
	opus_library = opus_module.create_static_library()

	if opus_library:
		return opus_library.opus_decoder_create(sample_rate, channel_total, ctypes.byref(ctypes.c_int(0)))

	return None


def decode(opus_decoder : OpusDecoder, input_buffer : Buffer, channel_total : int) -> Buffer:
	opus_library = opus_module.create_static_library()
	output_buffer = bytes()

	if opus_library:
		input_total = len(input_buffer)
		sample_size = ctypes.sizeof(ctypes.c_float)
		sample_total = opus_library.opus_decoder_get_nb_samples(opus_decoder, input_buffer, input_total)
		sample_buffer = (ctypes.c_float * (sample_total * channel_total))()
		output_total = opus_library.opus_decode_float(opus_decoder, input_buffer, input_total, sample_buffer, sample_total, 0)

		if output_total:
			output_buffer = ctypes.string_at(ctypes.addressof(sample_buffer), output_total * channel_total * sample_size)

	return output_buffer


def destroy(opus_decoder : OpusDecoder) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_decoder_destroy(opus_decoder)
