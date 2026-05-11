import ctypes
from typing import Optional

from facefusion.libraries import opus as opus_module


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


# TODO not 100 sure this makes full sense. should we not run clear on the lru-cache instead?
def destroy_opus_encoder(opus_encoder : ctypes.c_void_p) -> None:
	opus_library = opus_module.create_static_library()

	if opus_library:
		opus_library.opus_encoder_destroy(opus_encoder)
