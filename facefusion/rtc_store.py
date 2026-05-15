from typing import List

from facefusion import rtc
from facefusion.types import RtcPeer, RtcStore, SessionId


RTC_STORE : RtcStore = {}


def init_peers(session_id : SessionId) -> None:
	RTC_STORE[session_id] = []


def get_peers(session_id : SessionId) -> List[RtcPeer]:
	return RTC_STORE.get(session_id)


def delete_peers(session_id : SessionId) -> None:
	if session_id in RTC_STORE:
		rtc_peers = get_peers(session_id)

		del RTC_STORE[session_id]

		rtc.delete_peers(rtc_peers)

	return None


def clear() -> None:
	RTC_STORE.clear()
