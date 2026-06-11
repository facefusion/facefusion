import ctypes
import threading
from functools import partial

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import FrameHandler


def create_receive_event(track : int, frame_handler : FrameHandler) -> threading.Event:
	datachannel_library = datachannel_module.create_static_library()
	receive_event = threading.Event()

	frame_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(partial(dispatch_frame, frame_handler))
	close_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(partial(dispatch_event, receive_event))
	datachannel_library.rtcSetFrameCallback(track, frame_callback)
	datachannel_library.rtcSetClosedCallback(track, close_callback)
	receive_event.frame_callback = frame_callback  # type: ignore[attr-defined]
	receive_event.close_callback = close_callback  # type: ignore[attr-defined]

	return receive_event


def dispatch_frame(frame_handler : FrameHandler, track : int, data : ctypes.c_void_p, size : int, info : ctypes.c_void_p, pointer : ctypes.c_void_p) -> None:
	frame_buffer = ctypes.string_at(data, size)
	frame_timestamp = ctypes.cast(info, ctypes.POINTER(ctypes.c_uint32)).contents.value
	frame_handler(frame_buffer, frame_timestamp)


def dispatch_event(event : threading.Event, track : int, pointer : ctypes.c_void_p) -> None:
	event.set()
