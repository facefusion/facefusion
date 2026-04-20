import ctypes
from functools import lru_cache
from typing import Dict, List, Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet, RtcPeer


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


def is_peer_connected(rtc_library : ctypes.CDLL, peers : List[RtcPeer]) -> bool:
	for rtc_peer in peers:
		video_track_id = rtc_peer.get('video_track')

		if video_track_id and rtc_library.rtcIsOpen(video_track_id):
			return True

	return False
