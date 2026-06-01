import ctypes
import struct
from typing import Optional

import cv2
import numpy

from facefusion.libraries import aom as aom_module
from facefusion.types import AomDecoder, VisionFrame


def create(thread_count : int) -> Optional[AomDecoder]:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_decoder = ctypes.create_string_buffer(128)
		aom_codec = ctypes.c_void_p.in_dll(aom_library, 'aom_codec_av1_dx_algo')
		config_buffer = ctypes.create_string_buffer(128)

		struct.pack_into('I', config_buffer, 0, thread_count)
		struct.pack_into('I', config_buffer, 12, 1)

		if aom_library.aom_codec_dec_init_ver(aom_decoder, ctypes.byref(aom_codec), config_buffer, 0, 22) == 0:
			return aom_decoder

	return None


def decode(aom_decoder : AomDecoder, input_buffer : bytes) -> Optional[VisionFrame]:
	aom_library = aom_module.create_static_library()

	if aom_library and input_buffer:
		input_total = len(input_buffer)
		temp_buffer = ctypes.create_string_buffer(input_buffer)

		if aom_library.aom_codec_decode(aom_decoder, temp_buffer, input_total, None) == 0:
			address = aom_library.aom_codec_get_frame(aom_decoder, ctypes.byref(ctypes.c_void_p(0)))

			if address:
				frame_width = ctypes.c_uint.from_address(address + 28).value & ~1
				frame_height = ctypes.c_uint.from_address(address + 32).value & ~1
				vision_frame = numpy.frombuffer(collect(address, frame_width, frame_height), dtype = numpy.uint8).reshape((frame_height * 3 // 2, frame_width))
				return cv2.cvtColor(vision_frame, cv2.COLOR_YUV2BGR_I420)

	return None


def collect(address : int, frame_width : int, frame_height : int) -> bytes:
	output_parts = []

	for index in range(3):
		plane_pointer = ctypes.c_void_p.from_address(address + 64 + index * 8).value
		stride = ctypes.c_int.from_address(address + 88 + index * 4).value
		plane_width = frame_width >> (index > 0)
		plane_height = frame_height >> (index > 0)

		if stride == plane_width:
			output_parts.append(ctypes.string_at(plane_pointer, plane_width * plane_height))
		else:
			for row in range(plane_height):
				output_parts.append(ctypes.string_at(plane_pointer + row * stride, plane_width))

	return bytes().join(output_parts)


def destroy(aom_decoder : AomDecoder) -> None:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_library.aom_codec_destroy(aom_decoder)
