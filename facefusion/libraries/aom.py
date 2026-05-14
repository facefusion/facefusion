import ctypes
from functools import lru_cache
from typing import Optional

from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url_by_provider
from facefusion.filesystem import resolve_relative_path
from facefusion.types import LibrarySet


@lru_cache
def create_static_library_set() -> Optional[LibrarySet]:
	if is_linux():
		return\
		{
			'hashes':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'linux/libaom.hash'),
					'path': resolve_relative_path('../.libraries/libaom.hash')
				}
			},
			'sources':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'linux/libaom.so'),
					'path': resolve_relative_path('../.libraries/libaom.so')
				}
			}
		}
	if is_macos():
		return\
		{
			'hashes':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'macos/libaom.hash'),
					'path': resolve_relative_path('../.libraries/libaom.hash')
				}
			},
			'sources':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'macos/libaom.dylib'),
					'path': resolve_relative_path('../.libraries/libaom.dylib')
				}
			}
		}
	if is_windows():
		return\
		{
			'hashes':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/aom.hash'),
					'path': resolve_relative_path('../.libraries/aom.hash')
				}
			},
			'sources':
			{
				'aom':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/aom.dll'),
					'path': resolve_relative_path('../.libraries/aom.dll')
				}
			}
		}

	return None


def pre_check() -> bool:
	library_hash_set = create_static_library_set().get('hashes')
	library_source_set = create_static_library_set().get('sources')

	return conditional_download_hashes(library_hash_set) and conditional_download_sources(library_source_set)


@lru_cache
def create_static_library() -> Optional[ctypes.CDLL]:
	library_path = create_static_library_set().get('sources').get('aom').get('path')

	if library_path:
		if is_windows():
			library = ctypes.CDLL(library_path, winmode = 0)
		else:
			library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.aom_codec_enc_config_default.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint ]
	library.aom_codec_enc_config_default.restype = ctypes.c_int

	library.aom_codec_enc_init_ver.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_int ]
	library.aom_codec_enc_init_ver.restype = ctypes.c_int

	library.aom_codec_encode.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64, ctypes.c_ulong, ctypes.c_long, ctypes.c_ulong ]
	library.aom_codec_encode.restype = ctypes.c_int

	library.aom_codec_get_cx_data.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p) ]
	library.aom_codec_get_cx_data.restype = ctypes.c_void_p

	library.aom_codec_destroy.argtypes = [ ctypes.c_void_p ]
	library.aom_codec_destroy.restype = ctypes.c_int

	library.aom_img_wrap.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p ]
	library.aom_img_wrap.restype = ctypes.c_void_p

	library.aom_codec_control.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_int ]
	library.aom_codec_control.restype = ctypes.c_int

	return library
