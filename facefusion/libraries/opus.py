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
		return 'linux/libopus.hash', 'linux/libopus.so'
	if is_macos():
		return 'macos/libopus.hash', 'macos/libopus.dylib'
	if is_windows():
		return 'windows/opus.hash', 'windows/opus.dll'
	return None


@lru_cache
def create_static_library_set() -> Dict[str, DownloadSet]:
	library_hash_path, library_source_path = resolve_library_paths()

	return\
	{
		'hashes':
		{
			'opus':
			{
				'url': resolve_download_url_by_provider('huggingface', 'libraries-4.0.0', library_hash_path),
				'path': resolve_relative_path('../.libraries/' + os.path.basename(library_hash_path))
			}
		},
		'sources':
		{
			'opus':
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

	library.opus_encode_float.argtypes = [ ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int ]
	library.opus_encode_float.restype = ctypes.c_int

	library.opus_encoder_destroy.argtypes = [ ctypes.c_void_p ]
	library.opus_encoder_destroy.restype = None

	library.opus_encoder_ctl.argtypes = [ ctypes.c_void_p, ctypes.c_int, ctypes.c_int ]
	library.opus_encoder_ctl.restype = ctypes.c_int

	return library
