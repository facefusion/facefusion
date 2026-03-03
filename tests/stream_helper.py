from typing import Dict

from aiortc import RTCPeerConnection, VideoStreamTrack


async def create_webrtc_offer() -> Dict[str, str]:
	connection = RTCPeerConnection()
	connection.addTrack(VideoStreamTrack())
	offer = await connection.createOffer()
	await connection.setLocalDescription(offer)
	offer_dict =\
	{
		'sdp': connection.localDescription.sdp,
		'type': connection.localDescription.type
	}
	await connection.close()
	return offer_dict
