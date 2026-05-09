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


# TODO: clean up peer connection on failed sdp negotiation, wrap in run_in_executor to avoid blocking async event loop
def add_rtc_viewer(session_id : SessionId, sdp_offer : SdpOffer) -> Optional[SdpAnswer]:
	if session_id in RTC_STREAMS:
		payload_types = rtc.parse_sdp_payload_types(sdp_offer)
		peer_connection : PeerConnection = rtc.create_peer_connection()
		audio_track : RtcAudioTrack = rtc.add_audio_track(peer_connection, 'sendonly', payload_types.get('opus', 111))
		video_track : RtcVideoTrack = rtc.add_video_track(peer_connection, 'sendonly', payload_types.get('vp8', 96))
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


# TODO: detect and remove dead peers
def send_rtc_video(session_id : SessionId, frame_buffer : bytes) -> None:
	rtc_peers = get_rtc_stream(session_id)

	if rtc_peers:
		rtc.send_video_to_peers(rtc_peers, frame_buffer)


def send_rtc_audio(session_id : SessionId, audio_buffer : bytes, audio_pts : int) -> None:
	rtc_peers = get_rtc_stream(session_id)

	if rtc_peers:
		rtc.send_audio_to_peers(rtc_peers, audio_buffer, audio_pts)
