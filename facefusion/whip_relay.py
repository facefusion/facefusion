import threading
from typing import Optional

from facefusion import logger

RELAY_PORT : int = 8891
_started : bool = False
_lock : threading.Lock = threading.Lock()


def get_whip_url(stream_path : str) -> str:
	from facefusion import rtc
	return 'http://localhost:' + str(rtc.WHEP_PORT) + '/' + stream_path + '/whip'


def get_whep_url(stream_path : str) -> str:
	from facefusion import rtc
	return 'http://localhost:' + str(rtc.WHEP_PORT) + '/' + stream_path + '/whep'


def start() -> None:
	global _started

	from facefusion import rtc

	if not rtc.lib:
		if not rtc.load_library():
			logger.warn('whip relay: libdatachannel not available', __name__)
			return

	if not rtc.running:
		rtc.start()

	_started = True
	logger.info('whip relay (python) ready on port ' + str(rtc.WHEP_PORT), __name__)


def stop() -> None:
	global _started
	_started = False


def wait_for_ready() -> bool:
	return _started


def is_session_ready(stream_path : str) -> bool:
	from facefusion import rtc
	return stream_path in rtc.sessions


def create_session(stream_path : str) -> int:
	from facefusion import rtc

	if not _started:
		start()

	if not rtc.lib:
		return 0

	rtp_port = rtc.create_rtp_session(stream_path)
	return rtp_port
