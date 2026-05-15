from typing import List

from facefusion import rtc
from facefusion.types import RtcPeer, RtcStore, SessionId


RTC_STORE : RtcStore = {}


def get_rtc_peers(session_id : SessionId) -> List[RtcPeer]:
	return RTC_STORE.get(session_id)


def create_rtc_peers(session_id : SessionId) -> None:
	RTC_STORE[session_id] = []


def destroy_rtc_peers(session_id : SessionId) -> None:
	rtc_peers = RTC_STORE.pop(session_id, None)

	if rtc_peers:
		rtc.delete_peers(rtc_peers)
