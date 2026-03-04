from aiortc import RTCPeerConnection, VideoStreamTrack

from facefusion.types import RtcOfferSet


async def create_rtc_offer() -> RtcOfferSet:
	rtc_connection = RTCPeerConnection()
	rtc_connection.addTrack(VideoStreamTrack())
	rtc_offer = await rtc_connection.createOffer()

	await rtc_connection.setLocalDescription(rtc_offer)

	rtc_offer_set : RtcOfferSet =\
	{
		'sdp': rtc_connection.localDescription.sdp,
		'type': rtc_connection.localDescription.type
	}

	await rtc_connection.close()

	return rtc_offer_set
