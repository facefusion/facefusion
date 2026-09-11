from typing import Optional

from facefusion import rtc
from facefusion.types import RtcPeer, RtcStore, SessionId

RTC_STORE : RtcStore = {}


def has_peer(session_id : SessionId) -> bool:
	return session_id in RTC_STORE


def get_peer(session_id : SessionId) -> Optional[RtcPeer]:
	return RTC_STORE.get(session_id)


def set_peer(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	RTC_STORE[session_id] = rtc_peer


def delete_peer(session_id : SessionId) -> None:
	if session_id in RTC_STORE:
		rtc.delete_peer(RTC_STORE.pop(session_id))


def clear() -> None:
	RTC_STORE.clear()
