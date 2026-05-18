import ctypes
from typing import Optional

from facefusion.libraries import vpx as vpx_module
from facefusion.types import VpxDecoder, VpxPointer


def create() -> Optional[VpxDecoder]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_decoder = ctypes.create_string_buffer(64)
		vpx_codec = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_dx_algo')

		if vpx_library.vpx_codec_dec_init_ver(vpx_decoder, ctypes.byref(vpx_codec), None, 0, 12) == 0:
			return vpx_decoder

	return None


def decode(vpx_decoder : VpxDecoder, input_buffer : bytes) -> Optional[VpxPointer]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if vpx_library.vpx_codec_decode(vpx_decoder, temp_buffer, input_total, None, 0) == 0:
			address = vpx_library.vpx_codec_get_frame(vpx_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if address:
				frame_width = ctypes.c_uint.from_address(address + 24).value & ~1
				frame_height = ctypes.c_uint.from_address(address + 28).value & ~1
				return VpxPointer(address = address, resolution = (frame_width, frame_height))

	return None


def collect(vpx_pointer : VpxPointer) -> ctypes.Array[ctypes.c_uint8]:
	frame_width, frame_height = vpx_pointer.get('resolution')
	address = vpx_pointer.get('address')
	output_size = frame_width * frame_height * 3 // 2
	output_array = (ctypes.c_uint8 * output_size)()
	output_address = ctypes.addressof(output_array)
	write_offset = 0

	for index in range(3):
		plane_pointer = ctypes.c_void_p.from_address(address + 48 + index * 8).value
		plane_width = frame_width >> (index > 0)
		plane_height = frame_height >> (index > 0)
		plane_size = plane_width * plane_height

		ctypes.memmove(output_address + write_offset, plane_pointer, plane_size)
		write_offset += plane_size

	return output_array


def destroy(vpx_decoder : VpxDecoder) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(vpx_decoder)
