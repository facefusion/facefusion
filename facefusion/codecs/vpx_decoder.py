import ctypes
import struct
from typing import Optional

from facefusion.libraries import vpx as vpx_module
from facefusion.types import VpxDecoder, VpxPointer, VxpVideoCodec


def create(video_codec : VxpVideoCodec, thread_count : int) -> Optional[VpxDecoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_decoder = ctypes.create_string_buffer(64)
		vpx_algo = 'vpx_codec_vp8_dx_algo'

		if video_codec == 'vp9':
			vpx_algo = 'vpx_codec_vp9_dx_algo'

		vpx_codec = ctypes.c_void_p.in_dll(vpx_library, vpx_algo)
		config_buffer = ctypes.create_string_buffer(128)

		struct.pack_into('I', config_buffer, 0, thread_count)

		if vpx_library.vpx_codec_dec_init_ver(vpx_decoder, ctypes.byref(vpx_codec), config_buffer, 0, 12) == 0:
			return vpx_decoder

	return None


def decode(vpx_decoder : VpxDecoder, input_buffer : bytes) -> Optional[VpxPointer]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = ctypes.create_string_buffer(input_buffer)

		if vpx_library.vpx_codec_decode(vpx_decoder, temp_buffer, input_total, None, 0) == 0:
			address = vpx_library.vpx_codec_get_frame(vpx_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if address:
				frame_width = ctypes.c_uint.from_address(address + 24).value & ~1
				frame_height = ctypes.c_uint.from_address(address + 28).value & ~1

				return VpxPointer(
					buffer = collect(address, frame_width, frame_height),
					resolution = (frame_width, frame_height)
				)

	return None


def collect(address : int, frame_width : int, frame_height : int) -> bytes:
	output_parts = []

	for index in range(3):
		plane_pointer = ctypes.c_void_p.from_address(address + 48 + index * 8).value
		stride = ctypes.c_int.from_address(address + 80 + index * 4).value
		plane_width = frame_width >> (index > 0)
		plane_height = frame_height >> (index > 0)

		if stride == plane_width:
			output_parts.append(ctypes.string_at(plane_pointer, plane_width * plane_height))
		else:
			for row in range(plane_height):
				output_parts.append(ctypes.string_at(plane_pointer + row * stride, plane_width))

	return bytes().join(output_parts)


def destroy(vpx_decoder : VpxDecoder) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(vpx_decoder)
