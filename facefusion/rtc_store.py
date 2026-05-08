from typing import List, Optional

from facefusion import rtc
from facefusion.types import PeerConnection, RtcAudioTrack, RtcPeer, RtcStreamStore, RtcVideoTrack, SdpAnswer, SdpOffer, SessionId

RTC_STREAMS : RtcStreamStore = {}


def get_rtc_stream(session_id : SessionId) -> Optional[List[RtcPeer]]:
	return RTC_STREAMS.get(session_id)


def create_rtc_stream(session_id : SessionId) -> None:
	RTC_STREAMS[session_id] = []


def destroy_rtc_stream(session_id : SessionId) -> None:
	rtc_peers = RTC_STREAMS.pop(session_id, None)

	if rtc_peers:
		rtc.delete_peers(rtc_peers)


def add_rtc_viewer(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	if session_id in RTC_STREAMS:
		peer_connection : PeerConnection = rtc.create_peer_connection()
		audio_track : RtcAudioTrack = rtc.add_audio_track(peer_connection, 'sendonly')
		video_track : RtcVideoTrack = rtc.add_video_track(peer_connection, 'sendonly')
		local_sdp = rtc.negotiate_sdp(peer_connection, sdp_offer)

		if local_sdp:
			rtc_peer : RtcPeer =\
			{
				'peer_connection': peer_connection,
				'video_track': video_track,
				'audio_track': audio_track
			}
			RTC_STREAMS[session_id].append(rtc_peer)

		return local_sdp

	return None


def send_rtc_frame(session_id : SessionId, frame_data : bytes) -> None:
	rtc_peers = get_rtc_stream(session_id)

	if rtc_peers:
		rtc.send_to_peers(rtc_peers, frame_data)
