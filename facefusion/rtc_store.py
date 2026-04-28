from typing import List, Optional

from facefusion import rtc
from facefusion.types import RtcPeer, RtcSdpAnswer, RtcSdpOffer, RtcStreamStore

RTC_STREAMS : RtcStreamStore = {} # TODO: tie lifetime to session_id so streams are cleaned up on session expiry


def get_rtc_stream(stream_path : str) -> Optional[List[RtcPeer]]:
	return RTC_STREAMS.get(stream_path)


def create_rtc_stream(stream_path : str) -> None:
	RTC_STREAMS[stream_path] = []


def destroy_rtc_stream(stream_path : str) -> None:
	peers = RTC_STREAMS.pop(stream_path, None)

	if peers:
		rtc.delete_peers(peers)


def add_rtc_viewer(stream_path : str, sdp_offer : RtcSdpOffer) -> Optional[RtcSdpAnswer]:
	peers = get_rtc_stream(stream_path)

	if peers:
		return rtc.handle_whep_offer(peers, sdp_offer)

	return None


def send_rtc_frame(stream_path : str, frame_data : bytes) -> None:
	peers = get_rtc_stream(stream_path)

	if peers:
		rtc.send_to_peers(peers, frame_data)
