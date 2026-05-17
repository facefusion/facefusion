from typing import List

from facefusion import rtc
from facefusion.types import PeerConnection, RtcPeer, RtcStore, SessionId


RTC_STORE : RtcStore = {}


def init_peers(session_id : SessionId) -> None:
	if session_id not in RTC_STORE:
		RTC_STORE[session_id] = []


def add_peer(session_id : SessionId, rtc_peer : RtcPeer) -> None:
	init_peers(session_id)
	RTC_STORE[session_id].append(rtc_peer)


def get_peers(session_id : SessionId) -> List[RtcPeer]:
	return RTC_STORE.get(session_id)


def delete_peer(session_id : SessionId, peer_connection : PeerConnection) -> None:
	if session_id in RTC_STORE:
		rtc_peers = RTC_STORE.get(session_id)

		for rtc_peer in rtc_peers:
			if rtc_peer.get('peer_connection') == peer_connection:
				rtc_peers.remove(rtc_peer)
				rtc.delete_peers([ rtc_peer ])
				break


def delete_peers(session_id : SessionId) -> None:
	if session_id in RTC_STORE:
		rtc_peers = get_peers(session_id)

		if rtc_peers:
			rtc.delete_peers(rtc_peers)
			del RTC_STORE[session_id]

	return None


def clear() -> None:
	RTC_STORE.clear()
