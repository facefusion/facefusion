import ctypes
import threading
from functools import partial


def create_event(track : int, datachannel_library : ctypes.CDLL) -> threading.Event:
	available_event = threading.Event()
	available_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)(partial(dispatch_event, available_event))
	datachannel_library.rtcSetAvailableCallback(track, available_callback)
	available_event.callback = available_callback  # type: ignore[attr-defined]
	return available_event


def dispatch_event(event : threading.Event, track : int, pointer : ctypes.c_void_p) -> None:
	event.set()
