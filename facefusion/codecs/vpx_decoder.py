import ctypes
from typing import Optional

from facefusion.libraries import vpx as vpx_module
from facefusion.types import Resolution, VpxDecoder


def create_vpx_decoder() -> Optional[VpxDecoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_decoder = ctypes.create_string_buffer(64)
		vpx_codec = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_dx_algo')

		if vpx_library.vpx_codec_dec_init_ver(vpx_decoder, ctypes.byref(vpx_codec), None, 0, 12) == 0:
			return vpx_decoder

	return None


#TODO: needs review
def decode(vpx_decoder : VpxDecoder, input_buffer : bytes) -> bytes:
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


#TODO: needs review - find better name
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
