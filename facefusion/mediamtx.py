import os
import shutil
import subprocess
import time
from typing import Optional

import httpx


MEDIAMTX_WHIP_PORT : int = 8889
MEDIAMTX_API_PORT : int = 9997
MEDIAMTX_PATH : str = 'stream'
MEDIAMTX_CONFIG : str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mediamtx.yml')
MEDIAMTX_FALLBACK_BINARY : str = '/home/henry/local/bin/mediamtx'


def get_whip_url() -> str:
	return 'http://localhost:' + str(MEDIAMTX_WHIP_PORT) + '/' + MEDIAMTX_PATH + '/whip'


def get_api_url() -> str:
	return 'http://localhost:' + str(MEDIAMTX_API_PORT)


def resolve_binary() -> str:
	mediamtx_path = shutil.which('mediamtx')

	if mediamtx_path:
		return mediamtx_path
	return MEDIAMTX_FALLBACK_BINARY


def start() -> Optional[subprocess.Popen[bytes]]:
	stop_stale()
	mediamtx_binary = resolve_binary()

	return subprocess.Popen(
		[ mediamtx_binary, MEDIAMTX_CONFIG ],
		stdout = subprocess.DEVNULL,
		stderr = subprocess.DEVNULL
	)


def stop(process : subprocess.Popen[bytes]) -> None:
	process.terminate()
	process.wait()


def stop_stale() -> None:
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
