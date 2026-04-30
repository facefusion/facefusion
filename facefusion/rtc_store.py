from typing import List, Optional

from facefusion import rtc
from facefusion.types import RtcPeer, RtcSdpAnswer, RtcSdpOffer, RtcStreamStore, SessionId

RTC_STREAMS : RtcStreamStore = {}


def get_rtc_stream(session_id : SessionId) -> Optional[List[RtcPeer]]:
	return RTC_STREAMS.get(session_id)


def create_rtc_stream(session_id : SessionId) -> None:
	RTC_STREAMS[session_id] = []


def destroy_rtc_stream(session_id : SessionId) -> None:
	peers = RTC_STREAMS.pop(session_id, None)

	if peers:
		rtc.delete_peers(peers)


def add_rtc_viewer(session_id : SessionId, sdp_offer : RtcSdpOffer) -> Optional[RtcSdpAnswer]:
	if session_id in RTC_STREAMS:
		return rtc.handle_whep_offer(RTC_STREAMS.get(session_id), sdp_offer)

	return None


def send_rtc_frame(session_id : SessionId, frame_data : bytes) -> None:
	peers = get_rtc_stream(session_id)

	if peers:
		rtc.send_to_peers(peers, frame_data)
