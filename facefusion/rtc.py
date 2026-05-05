import ctypes
import os
import threading
import time
from functools import lru_cache
from typing import Dict, List, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.filesystem import resolve_relative_path
from facefusion.rtc_bindings import RTC_CONFIGURATION, RTC_PACKETIZER_INIT, init_ctypes
from facefusion.types import DownloadSet, RtcAudioTrack, RtcPeer, RtcSdpAnswer, RtcSdpOffer, RtcVideoTrack


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


@lru_cache
def create_static_rtc_library() -> Optional[ctypes.CDLL]:
	binary_path = create_static_download_set().get('sources').get('datachannel').get('path')

	if binary_path:
		rtc_library = ctypes.CDLL(binary_path)
		return init_ctypes(rtc_library)

	return None


def create_peer_connection(
	ice_servers : Optional[ctypes.Array[ctypes.c_char_p]] = None,
	ice_servers_count : int = 0, proxy_server : Optional[bytes] = None,
	bind_address : Optional[bytes] = None, certificate_type : int = 0,
	ice_transport_policy : int = 0,
	enable_ice_tcp : bool = False,
	enable_ice_udp_mux : bool = True,
	disable_auto_negotiation : bool = False,
	force_media_transport : bool = True,
	port_range_begin : int = 0,
	port_range_end : int = 0,
	max_packet_size : int = 0,
	max_message_size : int = 0) -> int:

	rtc_library = create_static_rtc_library()
	rtc_configuration = RTC_CONFIGURATION()

	rtc_configuration.iceServers = ice_servers
	rtc_configuration.iceServersCount = ice_servers_count
	rtc_configuration.proxyServer = proxy_server
	rtc_configuration.bindAddress = bind_address
	rtc_configuration.certificateType = certificate_type
	rtc_configuration.iceTransportPolicy = ice_transport_policy
	rtc_configuration.enableIceTcp = enable_ice_tcp
	rtc_configuration.enableIceUdpMux = enable_ice_udp_mux
	rtc_configuration.disableAutoNegotiation = disable_auto_negotiation
	rtc_configuration.forceMediaTransport = force_media_transport
	rtc_configuration.portRangeBegin = port_range_begin
	rtc_configuration.portRangeEnd = port_range_end
	rtc_configuration.mtu = max_packet_size
	rtc_configuration.maxMessageSize = max_message_size

	return rtc_library.rtcCreatePeerConnection(ctypes.byref(rtc_configuration))


def add_audio_track(peer_connection : int, sync_source_id : int = 43, canonical_name : bytes = b'audio', payload_type : int = 111, clock_rate : int = 48000) -> RtcAudioTrack:
	rtc_library = create_static_rtc_library()
	media_description = os.linesep.join(
	[
		'm=audio 9 UDP/TLS/RTP/SAVPF 111',
		'a=rtpmap:111 opus/48000/2',
		'a=sendonly',
		'a=mid:1',
		'a=rtcp-mux',
		''
	]).encode()

	audio_track = rtc_library.rtcAddTrack(peer_connection, media_description)

	audio_packetizer = RTC_PACKETIZER_INIT()
	audio_packetizer.ssrc = sync_source_id
	audio_packetizer.cname = canonical_name
	audio_packetizer.payloadType = payload_type
	audio_packetizer.clockRate = clock_rate

	rtc_library.rtcSetOpusPacketizer(audio_track, ctypes.byref(audio_packetizer))
	rtc_library.rtcChainRtcpSrReporter(audio_track)

	return audio_track


def add_video_track(peer_connection : int, sync_source_id : int = 42, canonical_name : bytes = b'video', payload_type : int = 96, clock_rate : int = 90000, max_fragment_size : int = 1200, nack_buffer_size : int = 512) -> RtcVideoTrack:
	rtc_library = create_static_rtc_library()
	media_description = os.linesep.join(
	[
		'm=video 9 UDP/TLS/RTP/SAVPF 96',
		'a=rtpmap:96 VP8/90000',
		'a=sendonly',
		'a=mid:0',
		'a=rtcp-mux',
		''
	]).encode()

	video_track = rtc_library.rtcAddTrack(peer_connection, media_description)

	video_packetizer = RTC_PACKETIZER_INIT()
	video_packetizer.ssrc = sync_source_id
	video_packetizer.cname = canonical_name
	video_packetizer.payloadType = payload_type
	video_packetizer.clockRate = clock_rate
	video_packetizer.maxFragmentSize = max_fragment_size

	rtc_library.rtcSetVP8Packetizer(video_track, ctypes.byref(video_packetizer))
	rtc_library.rtcChainRtcpSrReporter(video_track)
	rtc_library.rtcChainRtcpNackResponder(video_track, nack_buffer_size)

	return video_track


@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
def on_sdp_ready(peer_id : int, sdp : bytes, sdp_type : int, context_pointer : int) -> None:
	ctypes.cast(context_pointer, ctypes.py_object).value.set()


def negotiate_sdp(peer_connection : int, sdp_offer : str) -> Optional[str]:
	rtc_library = create_static_rtc_library()
	sdp_ready_event = threading.Event()

	rtc_library.rtcSetUserPointer(peer_connection, id(sdp_ready_event))
	rtc_library.rtcSetLocalDescriptionCallback(peer_connection, on_sdp_ready)
	rtc_library.rtcSetRemoteDescription(peer_connection, sdp_offer.encode('utf-8'), b'offer')

	sdp_ready_event.wait(timeout = 5)
	sdp_buffer_size = 16384
	sdp_buffer = ctypes.create_string_buffer(sdp_buffer_size)

	if rtc_library.rtcGetLocalDescription(peer_connection, sdp_buffer, sdp_buffer_size) > 0:
		return sdp_buffer.value.decode()

	return None


def handle_whep_offer(peers : List[RtcPeer], sdp_offer : RtcSdpOffer) -> Optional[RtcSdpAnswer]:
	peer_connection = create_peer_connection()
	audio_track = add_audio_track(peer_connection)
	video_track = add_video_track(peer_connection)
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
	rtc_library = create_static_rtc_library()

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
	rtc_library = create_static_rtc_library()

	for rtc_peer in peers:
		peer_connection_id = rtc_peer.get('peer_connection')

		if peer_connection_id:
			rtc_library.rtcDeletePeerConnection(peer_connection_id)

	peers.clear()


def is_peer_connected(peers : List[RtcPeer]) -> bool:
	rtc_library = create_static_rtc_library()

	for rtc_peer in peers:
		video_track_id = rtc_peer.get('video_track')

		if video_track_id and rtc_library.rtcIsOpen(video_track_id):
			return True

	return False
