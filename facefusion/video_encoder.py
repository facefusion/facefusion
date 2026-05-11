import ctypes
import multiprocessing
import struct
from collections import deque
from typing import Optional

import cv2

from facefusion import rtc_store
from facefusion.libraries import vpx as vpx_module
from facefusion.streamer import process_vision_frame
from facefusion.types import Resolution, SessionId, VisionFrame


# TODO this method needs refinement
def create_vpx_encoder(width : int, height : int, bitrate : int) -> Optional[ctypes.Array[ctypes.c_char]]:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vp8_descriptor = ctypes.c_void_p.in_dll(vpx_library, 'vpx_codec_vp8_cx_algo')
		config_buffer = ctypes.create_string_buffer(4096)

		if vpx_library.vpx_codec_enc_config_default(ctypes.byref(vp8_descriptor), config_buffer, 0) == 0:
			thread_count = min(multiprocessing.cpu_count(), 8)
			struct.pack_into('I', config_buffer, 4, thread_count)
			struct.pack_into('I', config_buffer, 12, width)
			struct.pack_into('I', config_buffer, 16, height)
			struct.pack_into('I', config_buffer, 72, 2)
			struct.pack_into('I', config_buffer, 112, bitrate)
			struct.pack_into('I', config_buffer, 116, 2)
			struct.pack_into('I', config_buffer, 120, 50)
			struct.pack_into('I', config_buffer, 124, 50)
			struct.pack_into('I', config_buffer, 128, 50)
			context_buffer = ctypes.create_string_buffer(512)

			if vpx_library.vpx_codec_enc_init_ver(context_buffer, ctypes.byref(vp8_descriptor), config_buffer, 0, 39) == 0:
				vpx_library.vpx_codec_control_(context_buffer, 13, ctypes.c_int(16))
				vpx_library.vpx_codec_control_(context_buffer, 12, ctypes.c_int(3))
				vpx_library.vpx_codec_control_(context_buffer, 27, ctypes.c_int(10))
				return context_buffer

	return None


# TODO this method needs refinement - rename to encode_vpx_buffer
def encode_vpx(codec_context : ctypes.Array[ctypes.c_char], yuv_buffer : bytes, width : int, height : int, presentation_timestamp : int, flags : int) -> bytes:
	vpx_library = vpx_module.create_static_library()
	frame_buffer = b''

	if vpx_library:
		image_buffer = ctypes.create_string_buffer(512)
		yuv_string_buffer = ctypes.create_string_buffer(yuv_buffer)

		if vpx_library.vpx_img_wrap(image_buffer, 0x102, width, height, 1, yuv_string_buffer):
			if vpx_library.vpx_codec_encode(codec_context, image_buffer, presentation_timestamp, 1, flags, 1) == 0:
				iterator = ctypes.c_void_p(0)
				packet = vpx_library.vpx_codec_get_cx_data(codec_context, ctypes.byref(iterator))

				while packet:
					if ctypes.c_int.from_address(packet).value == 0:
						buffer_pointer = ctypes.c_void_p.from_address(packet + 8).value
						buffer_size = ctypes.c_size_t.from_address(packet + 16).value
						frame_buffer += ctypes.string_at(buffer_pointer, buffer_size)

					packet = vpx_library.vpx_codec_get_cx_data(codec_context, ctypes.byref(iterator))

	return frame_buffer


# TODO not 100 sure this makes full sense. should we not run clear on the lru-cache instead?
def destroy_vpx_encoder(codec_context : ctypes.Array[ctypes.c_char]) -> None:
	vpx_library = vpx_module.create_static_library()

	if vpx_library:
		vpx_library.vpx_codec_destroy(codec_context)


# TODO: throttle loop to avoid spinning on same frame
def run_video_encode_loop(vision_frame_deque : deque[VisionFrame], session_id : SessionId, initial_resolution : Resolution, keyframe_interval : int) -> None:
	codec_context = create_vpx_encoder(initial_resolution[0], initial_resolution[1], 4500)
	current_resolution = initial_resolution
	pts = 0

	while vision_frame_deque:
		vision_frame = vision_frame_deque[-1]
		output_frame = process_vision_frame(vision_frame)
		height, width = output_frame.shape[:2]
		frame_resolution = (width, height)

		if frame_resolution[0] != current_resolution[0] or frame_resolution[1] != current_resolution[1]:
			if codec_context:
				destroy_vpx_encoder(codec_context)

			current_resolution = frame_resolution
			codec_context = create_vpx_encoder(current_resolution[0], current_resolution[1], 4500)
			pts = 0

		if codec_context:
			yuv_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2YUV_I420)
			vpx_flags = 0

			if pts % keyframe_interval == 0:
				vpx_flags = 1

			frame_buffer = encode_vpx(codec_context, yuv_frame.tobytes(), width, height, pts, vpx_flags)

			if frame_buffer:
				rtc_store.send_rtc_video(session_id, frame_buffer)

		pts += 1

	if codec_context:
		destroy_vpx_encoder(codec_context)
