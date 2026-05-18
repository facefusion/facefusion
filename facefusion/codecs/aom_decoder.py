import ctypes
from typing import Optional

from facefusion.libraries import aom as aom_module
from facefusion.types import AomDecoder, AomPointer


def create() -> Optional[AomDecoder]:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_decoder = ctypes.create_string_buffer(128)
		aom_codec = ctypes.c_void_p.in_dll(aom_library, 'aom_codec_av1_dx_algo')

		if aom_library.aom_codec_dec_init_ver(aom_decoder, ctypes.byref(aom_codec), None, 0, 22) == 0:
			return aom_decoder

	return None


def decode(aom_decoder : AomDecoder, input_buffer : bytes) -> Optional[AomPointer]:
	aom_library = aom_module.create_static_library()

	if aom_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = (ctypes.c_uint8 * input_total).from_buffer_copy(input_buffer)

		if aom_library.aom_codec_decode(aom_decoder, temp_buffer, input_total, None) == 0:
			address = aom_library.aom_codec_get_frame(aom_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if address:
				frame_width = ctypes.c_uint.from_address(address + 28).value & ~1
				frame_height = ctypes.c_uint.from_address(address + 32).value & ~1
				return AomPointer(address = address, resolution = (frame_width, frame_height))

	return None


def collect(aom_pointer : AomPointer) -> ctypes.Array[ctypes.c_uint8]:
	frame_width, frame_height = aom_pointer.get('resolution')
	address = aom_pointer.get('address')
	output_size = frame_width * frame_height * 3 // 2
	output_array = (ctypes.c_uint8 * output_size)()
	output_address = ctypes.addressof(output_array)
	write_offset = 0

	for index in range(3):
		plane_pointer = ctypes.c_void_p.from_address(address + 64 + index * 8).value
		plane_width = frame_width >> (index > 0)
		plane_height = frame_height >> (index > 0)
		plane_size = plane_width * plane_height

		ctypes.memmove(output_address + write_offset, plane_pointer, plane_size)
		write_offset += plane_size

	return output_array


def destroy(aom_decoder : AomDecoder) -> None:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_library.aom_codec_destroy(aom_decoder)
