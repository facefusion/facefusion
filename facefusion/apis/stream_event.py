import ctypes
import threading
from collections import deque
from functools import partial

import numpy

from facefusion.libraries import datachannel as datachannel_module
from facefusion.types import AudioPack, FrameCallback, FrameHandler, VideoPack


#todo - frame callback is very general name - this happens on sender or reciever, not clear at all
def create_frame_callback(track : int, handler : FrameHandler) -> FrameCallback:
	datachannel_library = datachannel_module.create_static_library()
	frame_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(handler)
	datachannel_library.rtcSetFrameCallback(track, frame_callback)
	return frame_callback


#todo - is done the correct name? - why not close?
def create_done_event(track : int, media_deque : deque[AudioPack] | deque[VideoPack], media_event : threading.Event) -> threading.Event:
	datachannel_library = datachannel_module.create_static_library()
	done_event = threading.Event()

	close_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(partial(dispatch_close, media_deque, media_event, done_event))
	datachannel_library.rtcSetClosedCallback(track, close_callback)
	done_event.callback = close_callback  # type: ignore[attr-defined]

	return done_event


#todo - bad name, cause it does not dispatch one even but two - also fills a queue which is absolute on the wrong spot here
def dispatch_close(media_deque : deque[AudioPack] | deque[VideoPack], media_event : threading.Event, done_event : threading.Event, track : int, pointer : ctypes.c_void_p) -> None:
	empty_frame = numpy.empty(0)
	media_deque.append((empty_frame, 0.0))
	media_event.set()
	done_event.set()
