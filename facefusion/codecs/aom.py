import ctypes
import struct
from typing import Optional

from facefusion.libraries import aom as aom_module
from facefusion.types import AomDecoder, AomEncoder, BitRate, Resolution


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
	output_buffer = bytes()

	if aom_library:
		temp_buffer = ctypes.create_string_buffer(256)
		encode_buffer = ctypes.create_string_buffer(input_buffer)

		if aom_library.aom_img_wrap(temp_buffer, 0x102, frame_resolution[0], frame_resolution[1], 1, encode_buffer) and aom_library.aom_codec_encode(aom_encoder, temp_buffer, frame_index, 1, 0, 1) == 0:
			output_buffer = collect_aom_buffer(aom_encoder)

	return output_buffer


def collect_aom_buffer(aom_encoder : AomEncoder) -> bytes:
	aom_library = aom_module.create_static_library()
	output_buffer = bytes()

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


def create_aom_decoder() -> Optional[AomDecoder]:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_decoder = ctypes.create_string_buffer(128)
		aom_codec = ctypes.c_void_p.in_dll(aom_library, 'aom_codec_av1_dx_algo')

		if aom_library.aom_codec_dec_init_ver(aom_decoder, ctypes.byref(aom_codec), None, 0, 22) == 0:
			return aom_decoder

	return None


#TODO: needs review
def decode_aom_buffer(aom_decoder : AomDecoder, input_buffer : bytes) -> bytes:
	aom_library = aom_module.create_static_library()
	output_buffer = bytes()

	if aom_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if aom_library.aom_codec_decode(aom_decoder, temp_buffer, input_total, None) == 0:
			frame_pointer = aom_library.aom_codec_get_frame(aom_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if frame_pointer:
				output_buffer = collect_aom_frame(frame_pointer)

	return output_buffer


#TODO: needs review
def collect_aom_frame(frame_pointer : int) -> bytes:
	frame_width = ctypes.c_uint.from_address(frame_pointer + 28).value
	frame_height = ctypes.c_uint.from_address(frame_pointer + 32).value
	planes_offset = frame_pointer + 64
	strides_offset = frame_pointer + 88
	output_buffer = bytes()

	for index in range(3):
		plane_pointer = ctypes.c_void_p.from_address(planes_offset + index * 8).value
		stride = ctypes.c_int.from_address(strides_offset + index * 4).value
		plane_width = frame_width >> (index > 0)
		plane_height = frame_height >> (index > 0)

		for row in range(plane_height):
			output_buffer += ctypes.string_at(plane_pointer + row * stride, plane_width)

	return output_buffer


#TODO: needs review
def read_aom_resolution(aom_decoder : AomDecoder, input_buffer : bytes) -> Optional[Resolution]:
	aom_library = aom_module.create_static_library()

	if aom_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if aom_library.aom_codec_decode(aom_decoder, temp_buffer, input_total, None) == 0:
			frame_pointer = aom_library.aom_codec_get_frame(aom_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if frame_pointer:
				frame_width = ctypes.c_uint.from_address(frame_pointer + 28).value
				frame_height = ctypes.c_uint.from_address(frame_pointer + 32).value
				return frame_width, frame_height

	return None


def destroy_aom_decoder(aom_decoder : AomDecoder) -> None:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_library.aom_codec_destroy(aom_decoder)
