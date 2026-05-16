import ctypes
import struct
from typing import Optional

import numpy

from facefusion.libraries import vpx as vpx_module
from facefusion.types import BitRate, Resolution, VisionFrame, VpxDecoder, VpxEncoder


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


#TODO: needs review
def create_vpx_decoder() -> Optional[VpxDecoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_decoder = ctypes.create_string_buffer(64)
		vpx_codec = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_dx_algo')

		if vpx_library.vpx_codec_dec_init_ver(vpx_decoder, ctypes.byref(vpx_codec), None, 0, 12) == 0:
			return vpx_decoder

	return None


#TODO: needs review
def decode_vpx_buffer(vpx_decoder : VpxDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library and frame_buffer:
		input_buffer = (ctypes.c_uint8 * len(frame_buffer)).from_buffer_copy(frame_buffer)

		if vpx_library.vpx_codec_decode(vpx_decoder, input_buffer, len(frame_buffer), None, 0) == 0:
			frame_cursor = ctypes.c_void_p(0)
			frame_pointer = vpx_library.vpx_codec_get_frame(vpx_decoder, ctypes.byref(frame_cursor))

			if frame_pointer:
				return extract_vpx_image(frame_pointer)

	return None


#TODO: needs review
def extract_vpx_image(frame_pointer : int) -> Optional[VisionFrame]:
	width = ctypes.c_uint.from_address(frame_pointer + 24).value
	height = ctypes.c_uint.from_address(frame_pointer + 28).value

	if width and height and width % 2 == 0 and height % 2 == 0:
		planes_offset = frame_pointer + 48
		strides_offset = frame_pointer + 80

		y_plane = extract_vpx_plane(planes_offset, strides_offset, 0, width, height)
		u_plane = extract_vpx_plane(planes_offset, strides_offset, 1, width // 2, height // 2)
		v_plane = extract_vpx_plane(planes_offset, strides_offset, 2, width // 2, height // 2)

		yuv_frame = numpy.concatenate([ y_plane.flatten(), u_plane.flatten(), v_plane.flatten() ])
		yuv_frame = yuv_frame.reshape((height * 3 // 2, width)).astype(numpy.uint8)

		return yuv_frame

	return None


#TODO: needs review
def extract_vpx_plane(planes_offset : int, strides_offset : int, index : int, width : int, height : int) -> numpy.ndarray:
	plane_pointer = ctypes.c_void_p.from_address(planes_offset + index * 8).value
	stride = ctypes.c_int.from_address(strides_offset + index * 4).value
	plane_buffer = (ctypes.c_ubyte * (stride * height)).from_address(plane_pointer)
	plane = numpy.ctypeslib.as_array(plane_buffer).reshape((height, stride))

	return plane[:, :width]


#TODO: needs review
def destroy_vpx_decoder(vpx_decoder : VpxDecoder) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(vpx_decoder)
