from typing import Dict

from aiortc import RTCPeerConnection, VideoStreamTrack


async def create_webrtc_offer() -> Dict[str, str]:
	rtc_connection = RTCPeerConnection()
	rtc_connection.addTrack(VideoStreamTrack())
	rtc_offer = await rtc_connection.createOffer()
	await rtc_connection.setLocalDescription(rtc_offer)
	offer_dict =\
	{
		'sdp': rtc_connection.localDescription.sdp,
		'type': rtc_connection.localDescription.type
	}
	await rtc_connection.close()
	return offer_dict
