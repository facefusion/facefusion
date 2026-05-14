import ctypes
import struct
from typing import Optional

from facefusion.libraries import aom as aom_module
from facefusion.types import AomEncoder, BitRate, Resolution


def create_aom_encoder(frame_resolution : Resolution, bitrate : BitRate, thread_count : int, cpu_count : int) -> Optional[AomEncoder]:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_encoder = ctypes.create_string_buffer(128)
		aom_codec = ctypes.c_void_p.in_dll(aom_library, 'aom_codec_av1_cx_algo')

		config_buffer = ctypes.create_string_buffer(1024)

		if aom_library.aom_codec_enc_config_default(ctypes.byref(aom_codec), config_buffer, 1) == 0:
			struct.pack_into('I', config_buffer, 4, thread_count)
			struct.pack_into('I', config_buffer, 12, frame_resolution[0])
			struct.pack_into('I', config_buffer, 16, frame_resolution[1])
			struct.pack_into('I', config_buffer, 136, bitrate)
			struct.pack_into('I', config_buffer, 192, 30)

			if aom_library.aom_codec_enc_init_ver(aom_encoder, ctypes.byref(aom_codec), config_buffer, 0, 25) == 0:
				aom_library.aom_codec_control(aom_encoder, 13, ctypes.c_int(cpu_count))
				aom_library.aom_codec_control(aom_encoder, 75, ctypes.c_int(2))
				aom_library.aom_codec_control(aom_encoder, 106, ctypes.c_int(1))
				aom_library.aom_codec_control(aom_encoder, 122, ctypes.c_int(0))
				aom_library.aom_codec_control(aom_encoder, 123, ctypes.c_int(0))
				return aom_encoder

	return None


def encode_aom_buffer(aom_encoder : AomEncoder, input_buffer : bytes, frame_resolution : Resolution, frame_index : int) -> bytes:
	aom_library = aom_module.create_static_library()
	output_buffer = b''

	if aom_library:
		temp_buffer = ctypes.create_string_buffer(256)
		encode_buffer = ctypes.create_string_buffer(input_buffer)

		if aom_library.aom_img_wrap(temp_buffer, 0x102, frame_resolution[0], frame_resolution[1], 1, encode_buffer) and aom_library.aom_codec_encode(aom_encoder, temp_buffer, frame_index, 1, 0, 1) == 0:
			output_buffer = collect_aom_buffer(aom_encoder)

	return output_buffer


def collect_aom_buffer(aom_encoder : AomEncoder) -> bytes:
	aom_library = aom_module.create_static_library()
	output_buffer = b''

	packet_cursor = ctypes.c_void_p(0)
	packet = aom_library.aom_codec_get_cx_data(aom_encoder, ctypes.byref(packet_cursor))

	while packet:
		if ctypes.c_int.from_address(packet).value == 0:
			buffer_pointer = ctypes.c_void_p.from_address(packet + 8).value
			buffer_size = ctypes.c_size_t.from_address(packet + 16).value
			output_buffer += ctypes.string_at(buffer_pointer, buffer_size)

		packet = aom_library.aom_codec_get_cx_data(aom_encoder, ctypes.byref(packet_cursor))

	return output_buffer


def destroy_aom_encoder(aom_encoder : AomEncoder) -> None:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_library.aom_codec_destroy(aom_encoder)
