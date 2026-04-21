import ctypes
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.filesystem import resolve_relative_path
from facefusion.rtc_bindings import RTC_CONFIGURATION, RTC_PACKETIZER_INIT, init_ctypes
from facefusion.types import DownloadSet, RtcAudioTrack, RtcPeer, RtcVideoTrack

RTC_LIBRARY: Optional[ctypes.CDLL] = None


def resolve_binary_file() -> Optional[str]:
	if is_linux():
		return 'linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so'
	if is_macos():
		return 'macos-universal-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.dylib'
	if is_windows():
		return 'windows-x64-openssl-h264-vp8-av1-opus-datachannel-0.24.1.dll'
	return None


@lru_cache
def create_static_download_set() -> Dict[str, DownloadSet]: # TODO: replace once conda package is in place
	binary_name = resolve_binary_file()

	return\
	{
		'hashes':
		{
			'datachannel':
			{
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so.hash', # TODO: use url with dynamic binary_name
				'path': resolve_relative_path('../.assets/binaries/' + binary_name + '.hash')
			}
		},
		'sources':
		{
			'datachannel':
			{
				'url': 'https://huggingface.co/bluefoxcreation/libdatachannel/resolve/main/linux-x64-openssl-h264-vp8-av1-opus-libdatachannel-0.24.1.so', # TODO: use url with dynamic binary_name
				'path': resolve_relative_path('../.assets/binaries/' + binary_name)
			}
		}
	}


def pre_check() -> bool:
	download_set = create_static_download_set()

	if not conditional_download_hashes(download_set.get('hashes')):
		return False
	return conditional_download_sources(download_set.get('sources'))


def get_rtc_library() -> Optional[ctypes.CDLL]:
	global RTC_LIBRARY

	if RTC_LIBRARY:
		return RTC_LIBRARY
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		rtc_library = ctypes.CDLL(binary_path)
		if init_ctypes(rtc_library):
			RTC_LIBRARY = rtc_library

	return RTC_LIBRARY


def create_peer_connection() -> int:
	rtc_library = get_rtc_library()
	config = RTC_CONFIGURATION()
	config.iceServers = None
	config.iceServersCount = 0
	config.proxyServer = None
	config.bindAddress = None
	config.certificateType = 0
	config.iceTransportPolicy = 0
	config.enableIceTcp = False
	config.enableIceUdpMux = True
	config.disableAutoNegotiation = False
	config.forceMediaTransport = True
	config.portRangeBegin = 0
	config.portRangeEnd = 0
	config.mtu = 0
	config.maxMessageSize = 0
	return rtc_library.rtcCreatePeerConnection(ctypes.byref(config))


def add_media_tracks(peer_connection : int) -> Tuple[RtcVideoTrack, RtcAudioTrack]:
	rtc_library = get_rtc_library()
	video_media_description = b'm=video 9 UDP/TLS/RTP/SAVPF 96\r\na=rtpmap:96 VP8/90000\r\na=sendonly\r\na=mid:0\r\na=rtcp-mux\r\n'
	audio_media_description = b'm=audio 9 UDP/TLS/RTP/SAVPF 111\r\na=rtpmap:111 opus/48000/2\r\na=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n'

	video_track = rtc_library.rtcAddTrack(peer_connection, video_media_description)
	audio_track = rtc_library.rtcAddTrack(peer_connection, audio_media_description)

	video_packetizer = RTC_PACKETIZER_INIT()
	video_packetizer.ssrc = 42
	video_packetizer.cname = b'video'
	video_packetizer.payloadType = 96
	video_packetizer.clockRate = 90000
	video_packetizer.maxFragmentSize = 1200
	rtc_library.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))
	rtc_library.rtcChainRtcpSrReporter(video_track)
	rtc_library.rtcChainRtcpNackResponder(video_track, 512)

	audio_packetizer = RTC_PACKETIZER_INIT()
	audio_packetizer.ssrc = 43
	audio_packetizer.cname = b'audio'
	audio_packetizer.payloadType = 111
	audio_packetizer.clockRate = 48000
	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)
	return video_track, audio_track


def negotiate_sdp(peer_connection : int, sdp_offer : str) -> Optional[str]:
	rtc_library = get_rtc_library()
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')
	buffer_size = 16384
	buffer_string = ctypes.create_string_buffer(buffer_size)
	wait_limit = time.monotonic() + 5

	while time.monotonic() < wait_limit:
		if rtc_library.rtcGetLocalDescription(peer_connection, buffer_string, buffer_size) > 0:
			return buffer_string.value.decode()
		time.sleep(0.05)

	return None


def handle_whep_offer(peers : List[RtcPeer], sdp_offer : str) -> Optional[str]:
	peer_connection = create_peer_connection()
	video_track, audio_track = add_media_tracks(peer_connection)
	local_sdp = negotiate_sdp(peer_connection, sdp_offer)

	if local_sdp:
		rtc_peer : RtcPeer =\
		{
			'peer_connection': peer_connection,
			'video_track': video_track,
			'audio_track': audio_track
		}
		peers.append(rtc_peer)

	return local_sdp


def send_to_peers(peers : List[RtcPeer], data : bytes) -> None:
	rtc_library = get_rtc_library()
	if peers:
		timestamp = int(time.monotonic() * 90000) & 0xFFFFFFFF
		data_buffer = ctypes.create_string_buffer(data)
		data_total = len(data)

		for rtc_peer in peers:
			video_track_id = rtc_peer.get('video_track')

			if video_track_id and rtc_library.rtcIsOpen(video_track_id):
				rtc_library.rtcSetTrackRtpTimestamp(video_track_id, timestamp)
				rtc_library.rtcSendMessage(video_track_id, data_buffer, data_total)

	return None


def delete_peers(peers : List[RtcPeer]) -> None:
	rtc_library = get_rtc_library()

	for rtc_peer in peers:
		peer_connection_id = rtc_peer.get('peer_connection')

		if peer_connection_id:
			rtc_library.rtcDeletePeerConnection(peer_connection_id)

	peers.clear()


def is_peer_connected(peers : List[RtcPeer]) -> bool:
	rtc_library = get_rtc_library()
	for rtc_peer in peers:
		video_track_id = rtc_peer.get('video_track')

		if video_track_id and rtc_library.rtcIsOpen(video_track_id):
			return True

	return False
