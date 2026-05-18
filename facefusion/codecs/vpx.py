import ctypes
import struct
from typing import Optional

from facefusion.libraries import vpx as vpx_module
from facefusion.types import BitRate, Resolution, VpxDecoder, VpxEncoder


def create_vpx_encoder(frame_resolution : Resolution, bitrate : BitRate, thread_count : int, cpu_count : int) -> Optional[VpxEncoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_encoder = ctypes.create_string_buffer(64)
		vp8_codec = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_cx_algo')

		config_buffer = ctypes.create_string_buffer(512)

		if vpx_library.vpx_codec_enc_config_default(ctypes.byref(vp8_codec), config_buffer, 0) == 0:
			struct.pack_into('I', config_buffer, 4, thread_count)
			struct.pack_into('I', config_buffer, 12, frame_resolution[0])
			struct.pack_into('I', config_buffer, 16, frame_resolution[1])
			struct.pack_into('I', config_buffer, 28, 1)
			struct.pack_into('I', config_buffer, 36, 0)
			struct.pack_into('I', config_buffer, 72, 0)
			struct.pack_into('I', config_buffer, 112, bitrate)
			struct.pack_into('I', config_buffer, 116, 2)
			struct.pack_into('I', config_buffer, 120, 50)
			struct.pack_into('I', config_buffer, 124, 50)
			struct.pack_into('I', config_buffer, 128, 50)

			if vpx_library.vpx_codec_enc_init_ver(vpx_encoder, ctypes.byref(vp8_codec), config_buffer, 0, 39) == 0:
				vpx_library.vpx_codec_control_(vpx_encoder, 13, ctypes.c_int(cpu_count))
				vpx_library.vpx_codec_control_(vpx_encoder, 12, ctypes.c_int(3))
				vpx_library.vpx_codec_control_(vpx_encoder, 27, ctypes.c_int(10))
				return vpx_encoder

	return None


def encode_vpx_buffer(vpx_encoder : VpxEncoder, input_buffer : bytes, frame_resolution : Resolution, frame_index : int) -> bytes:
	vpx_library = vpx_module.create_static_library()
	output_buffer = bytes()

	if vpx_library:
		temp_buffer = ctypes.create_string_buffer(256)
		encode_buffer = ctypes.create_string_buffer(input_buffer)

		if vpx_library.vpx_img_wrap(temp_buffer, 0x102, frame_resolution[0], frame_resolution[1], 1, encode_buffer) and vpx_library.vpx_codec_encode(vpx_encoder, temp_buffer, frame_index, 1, 0, 1) == 0:
			output_buffer = collect_vpx_buffer(vpx_encoder)

	return output_buffer


def collect_vpx_buffer(vpx_encoder : VpxEncoder) -> bytes:
	vpx_library = vpx_module.create_static_library()
	output_buffer = bytes()

	packet_cursor = ctypes.c_void_p(0)
	packet = vpx_library.vpx_codec_get_cx_data(vpx_encoder, ctypes.byref(packet_cursor))

	while packet:
		if ctypes.c_int.from_address(packet).value == 0:
			buffer_pointer = ctypes.c_void_p.from_address(packet + 8).value
			buffer_size = ctypes.c_size_t.from_address(packet + 16).value
			output_buffer += ctypes.string_at(buffer_pointer, buffer_size)

		packet = vpx_library.vpx_codec_get_cx_data(vpx_encoder, ctypes.byref(packet_cursor))

	return output_buffer


def destroy_vpx_encoder(vpx_encoder : VpxEncoder) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(vpx_encoder)


def create_vpx_decoder() -> Optional[VpxDecoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_decoder = ctypes.create_string_buffer(64)
		vpx_codec = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_dx_algo')

		if vpx_library.vpx_codec_dec_init_ver(vpx_decoder, ctypes.byref(vpx_codec), None, 0, 12) == 0:
			return vpx_decoder

	return None


#TODO: needs review
def decode_vpx_buffer(vpx_decoder : VpxDecoder, input_buffer : bytes) -> bytes:
	vpx_library = vpx_module.create_static_library()
	output_buffer = bytes()

	if vpx_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if vpx_library.vpx_codec_decode(vpx_decoder, temp_buffer, input_total, None, 0) == 0:
			frame_pointer = vpx_library.vpx_codec_get_frame(vpx_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if frame_pointer:
				output_buffer = collect_vpx_frame(frame_pointer)

	return output_buffer


#TODO: needs review
def collect_vpx_frame(frame_pointer : int) -> bytes:
	frame_width = ctypes.c_uint.from_address(frame_pointer + 24).value
	frame_height = ctypes.c_uint.from_address(frame_pointer + 28).value
	planes_offset = frame_pointer + 48
	strides_offset = frame_pointer + 80
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
def read_vpx_resolution(vpx_decoder : VpxDecoder, input_buffer : bytes) -> Optional[Resolution]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if vpx_library.vpx_codec_decode(vpx_decoder, temp_buffer, input_total, None, 0) == 0:
			frame_pointer = vpx_library.vpx_codec_get_frame(vpx_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if frame_pointer:
				frame_width = ctypes.c_uint.from_address(frame_pointer + 24).value
				frame_height = ctypes.c_uint.from_address(frame_pointer + 28).value
				return frame_width, frame_height

	return None


def destroy_vpx_decoder(vpx_decoder : VpxDecoder) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(vpx_decoder)
