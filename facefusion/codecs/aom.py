import ctypes
import struct
from typing import Optional

import numpy

from facefusion.libraries import aom as aom_module
from facefusion.types import AomDecoder, AomEncoder, BitRate, Resolution, VisionFrame


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


def add_obu_size_field(frame_buffer : bytes) -> bytes:
	header_byte = frame_buffer[0]
	has_size = (header_byte >> 1) & 1

	if has_size:
		return frame_buffer

	has_extension = (header_byte >> 2) & 1
	header_size = 2 if has_extension else 1
	payload_size = len(frame_buffer) - header_size
	size_bytes = encode_leb128(payload_size)

	return bytes([header_byte | 0x02]) + frame_buffer[1:header_size] + size_bytes + frame_buffer[header_size:]


def encode_leb128(value : int) -> bytes:
	result = bytearray()

	while value >= 0x80:
		result.append((value & 0x7F) | 0x80)
		value >>= 7

	result.append(value & 0x7F)

	return bytes(result)


def decode_aom_buffer(aom_decoder : AomDecoder, frame_buffer : bytes) -> Optional[VisionFrame]:
	aom_library = aom_module.create_static_library()

	if aom_library and frame_buffer:
		sized_buffer = add_obu_size_field(frame_buffer)
		input_buffer = (ctypes.c_uint8 * len(sized_buffer)).from_buffer_copy(sized_buffer)

		if aom_library.aom_codec_decode(aom_decoder, input_buffer, len(sized_buffer), None) != 0:
			return None

		frame_cursor = ctypes.c_void_p(0)
		frame_pointer = aom_library.aom_codec_get_frame(aom_decoder, ctypes.byref(frame_cursor))

		if frame_pointer:
			return extract_aom_image(frame_pointer)

	return None


def extract_aom_image(frame_pointer : int) -> Optional[VisionFrame]:
	width = ctypes.c_uint.from_address(frame_pointer + 28).value
	height = ctypes.c_uint.from_address(frame_pointer + 32).value

	if width and height and width % 2 == 0 and height % 2 == 0:
		planes_offset = frame_pointer + 64
		strides_offset = frame_pointer + 88

		y_plane = extract_aom_plane(planes_offset, strides_offset, 0, width, height)
		u_plane = extract_aom_plane(planes_offset, strides_offset, 1, width // 2, height // 2)
		v_plane = extract_aom_plane(planes_offset, strides_offset, 2, width // 2, height // 2)

		yuv_frame = numpy.concatenate([ y_plane.flatten(), u_plane.flatten(), v_plane.flatten() ])
		yuv_frame = yuv_frame.reshape((height * 3 // 2, width)).astype(numpy.uint8)

		return yuv_frame

	return None


def extract_aom_plane(planes_offset : int, strides_offset : int, index : int, width : int, height : int) -> numpy.ndarray:
	plane_pointer = ctypes.c_void_p.from_address(planes_offset + index * 8).value
	stride = ctypes.c_int.from_address(strides_offset + index * 4).value
	plane_buffer = (ctypes.c_ubyte * (stride * height)).from_address(plane_pointer)
	plane = numpy.ctypeslib.as_array(plane_buffer).reshape((height, stride))

	return plane[:, :width]


def destroy_aom_decoder(aom_decoder : AomDecoder) -> None:
	aom_library = aom_module.create_static_library()

	if aom_library:
		aom_library.aom_codec_destroy(aom_decoder)
