import ctypes
import os
from functools import lru_cache
from typing import Dict, Optional, Tuple

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url_by_provider
from facefusion.filesystem import resolve_relative_path
from facefusion.types import DownloadSet


def resolve_library_paths() -> Optional[Tuple[str, str]]:
	if is_linux():
		return 'linux/libvpx.hash', 'linux/libvpx.so'
	if is_macos():
		return 'macos/libvpx.hash', 'macos/libvpx.dylib'
	if is_windows():
		return 'windows/vpx.hash', 'windows/vpx.dll'
	return None


@lru_cache
def create_static_library_set() -> Dict[str, DownloadSet]:
	library_hash_path, library_source_path = resolve_library_paths()

	return\
	{
		'hashes':
		{
			'vpx':
			{
				'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', library_hash_path),
				'path': resolve_relative_path('../.libraries/' + os.path.basename(library_hash_path))
			}
		},
		'sources':
		{
			'vpx':
			{
				'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', library_source_path),
				'path': resolve_relative_path('../.libraries/' + os.path.basename(library_source_path))
			}
		}
	}


def pre_check() -> bool:
	library_hash_set = create_static_library_set().get('hashes')
	library_source_set = create_static_library_set().get('sources')

	return conditional_download_hashes(library_hash_set) and conditional_download_sources(library_source_set)


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = create_static_library_set().get('sources').get('vpx').get('path')

	if library_path:
		if is_windows():
			library = ctypes.CDLL(library_path, winmode = 0)
		else:
			library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.vpx_codec_enc_config_default.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint ]
	library.vpx_codec_enc_config_default.restype = ctypes.c_int

	library.vpx_codec_enc_init_ver.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_int ]
	library.vpx_codec_enc_init_ver.restype = ctypes.c_int

	library.vpx_codec_encode.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64, ctypes.c_ulong, ctypes.c_long, ctypes.c_ulong ]
	library.vpx_codec_encode.restype = ctypes.c_int

	library.vpx_codec_get_cx_data.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p) ]
	library.vpx_codec_get_cx_data.restype = ctypes.c_void_p

	library.vpx_codec_destroy.argtypes = [ ctypes.c_void_p ]
	library.vpx_codec_destroy.restype = ctypes.c_int

	library.vpx_img_wrap.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p ]
	library.vpx_img_wrap.restype = ctypes.c_void_p

	library.vpx_codec_control_.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_int ]
	library.vpx_codec_control_.restype = ctypes.c_int

	return library
