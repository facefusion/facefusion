import os
import shutil
import subprocess
import time
from typing import Optional

import httpx

from facefusion.common_helper import is_linux


MEDIAMTX_WHIP_PORT : int = 8889
MEDIAMTX_API_PORT : int = 9997
MEDIAMTX_CONFIG : str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mediamtx.yml')
MEDIAMTX_FALLBACK_BINARY : str = '/home/henry/local/bin/mediamtx'
MEDIAMTX_PROCESS : Optional[subprocess.Popen[bytes]] = None


def get_whip_url(stream_path : str) -> str:
	return 'http://localhost:' + str(MEDIAMTX_WHIP_PORT) + '/' + stream_path + '/whip'


def get_whep_url(stream_path : str) -> str:
	return 'http://localhost:' + str(MEDIAMTX_WHIP_PORT) + '/' + stream_path + '/whep'


def get_api_url() -> str:
	return 'http://localhost:' + str(MEDIAMTX_API_PORT)


def resolve_binary() -> str:
	mediamtx_path = shutil.which('mediamtx')

	if mediamtx_path:
		return mediamtx_path
	return MEDIAMTX_FALLBACK_BINARY


def start() -> None:
	global MEDIAMTX_PROCESS

	stop_stale()
	mediamtx_binary = resolve_binary()
	MEDIAMTX_PROCESS = subprocess.Popen(
		[ mediamtx_binary, MEDIAMTX_CONFIG ],
		stdout = subprocess.DEVNULL,
		stderr = subprocess.DEVNULL
	)


def stop() -> None:
	global MEDIAMTX_PROCESS

	if MEDIAMTX_PROCESS:
		MEDIAMTX_PROCESS.terminate()
		MEDIAMTX_PROCESS.wait()
		MEDIAMTX_PROCESS = None


def stop_stale() -> None:
	if is_linux():
		subprocess.run([ 'fuser', '-k', str(MEDIAMTX_WHIP_PORT) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', '8189/udp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ 'fuser', '-k', str(MEDIAMTX_API_PORT) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	time.sleep(1)


def wait_for_ready() -> bool:
	api_url = get_api_url() + '/v3/paths/list'

	for _ in range(10):
		try:
			response = httpx.get(api_url, timeout = 1)

			if response.status_code == 200:
				return True
		except Exception:
			pass
		time.sleep(0.5)
	return False


def is_path_ready(stream_path : str) -> bool:
	api_url = get_api_url() + '/v3/paths/get/' + stream_path

	try:
		response = httpx.get(api_url, timeout = 1)

		if response.status_code == 200:
			return response.json().get('ready', False)
	except Exception:
		pass
	return False


def add_path(stream_path : str) -> bool:
	api_url = get_api_url() + '/v3/config/paths/add/' + stream_path
	response = httpx.post(api_url, json = {}, timeout = 5)

	return response.status_code == 200


def remove_path(stream_path : str) -> bool:
	api_url = get_api_url() + '/v3/config/paths/delete/' + stream_path
	response = httpx.delete(api_url, timeout = 5)

	return response.status_code == 200
