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
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'linux/libopus.hash'),
					'path': resolve_relative_path('../.libraries/libopus.hash')
				}
			},
			'sources':
			{
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'linux/libopus.so'),
					'path': resolve_relative_path('../.libraries/libopus.so')
				}
			}
		}

	if is_macos():
		return\
		{
			'hashes':
			{
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'macos/libopus.hash'),
					'path': resolve_relative_path('../.libraries/libopus.hash')
				}
			},
			'sources':
			{
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'macos/libopus.dylib'),
					'path': resolve_relative_path('../.libraries/libopus.dylib')
				}
			}
		}

	if is_windows():
		return\
		{
			'hashes':
			{
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/opus.hash'),
					'path': resolve_relative_path('../.libraries/opus.hash')
				}
			},
			'sources':
			{
				'opus':
				{
					'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', 'windows/opus.dll'),
					'path': resolve_relative_path('../.libraries/opus.dll')
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
	library_path = create_static_library_set().get('sources').get('opus').get('path')

	if library_path:
		if is_windows():
			library = ctypes.CDLL(library_path, winmode = 0)
		else:
			library = ctypes.CDLL(library_path)

		if library:
			return init_ctypes(library)

	return None


def init_ctypes(library : ctypes.CDLL) -> ctypes.CDLL:
	library.opus_encoder_create.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int) ]
	library.opus_encoder_create.restype = ctypes.c_void_p

	library.opus_encode_float.argtypes = [ ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	library.opus_encode_float.restype = ctypes.c_int

	library.opus_encoder_destroy.argtypes = [ ctypes.c_void_p ]
	library.opus_encoder_destroy.restype = None

	library.opus_decoder_create.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int) ]
	library.opus_decoder_create.restype = ctypes.c_void_p

	library.opus_decode_float.argtypes = [ ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int ]
	library.opus_decode_float.restype = ctypes.c_int

	library.opus_decoder_destroy.argtypes = [ ctypes.c_void_p ]
	library.opus_decoder_destroy.restype = None

	return library
