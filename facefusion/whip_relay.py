import os
import shutil
import subprocess
import time
from typing import Optional

import httpx

from facefusion import logger

RELAY_PORT : int = 8891
RELAY_BINARY : str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'whip_relay')
RELAY_PROCESS : Optional[subprocess.Popen[bytes]] = None


def get_whip_url(stream_path : str) -> str:
	return 'http://localhost:' + str(RELAY_PORT) + '/' + stream_path + '/whip'


def get_whep_url(stream_path : str) -> str:
	return 'http://localhost:' + str(RELAY_PORT) + '/' + stream_path + '/whep'


def resolve_binary() -> str:
	relay_path = shutil.which('whip_relay')

	if relay_path:
		return relay_path

	if os.path.isfile(RELAY_BINARY):
		return RELAY_BINARY
	return RELAY_BINARY


def start() -> None:
	global RELAY_PROCESS

	subprocess.run([ 'fuser', '-k', str(RELAY_PORT) + '/tcp' ], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	time.sleep(0.5)

	relay_binary = resolve_binary()

	if not os.path.isfile(relay_binary):
		logger.warn('whip_relay binary not found at ' + relay_binary + ', skipping', __name__)
		return

	env = os.environ.copy()
	env['LD_LIBRARY_PATH'] = '/home/henry/local/lib:' + env.get('LD_LIBRARY_PATH', '')
	RELAY_PROCESS = subprocess.Popen(
		[ relay_binary, str(RELAY_PORT) ],
		env = env,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE
	)
	logger.info('whip relay started on port ' + str(RELAY_PORT), __name__)


def stop() -> None:
	global RELAY_PROCESS

	if RELAY_PROCESS:
		RELAY_PROCESS.terminate()
		RELAY_PROCESS.wait()
		RELAY_PROCESS = None


def wait_for_ready() -> bool:
	for _ in range(10):
		try:
			response = httpx.get('http://localhost:' + str(RELAY_PORT) + '/health', timeout = 1)

			if response.status_code == 200:
				return True
		except Exception:
			pass
		time.sleep(0.5)
	return False


def is_session_ready(stream_path : str) -> bool:
	try:
		response = httpx.get('http://localhost:' + str(RELAY_PORT) + '/session/' + stream_path, timeout = 1)

		if response.status_code == 200:
			return True
	except Exception:
		pass
	return False


def create_session(stream_path : str) -> int:
	try:
		response = httpx.post('http://localhost:' + str(RELAY_PORT) + '/' + stream_path + '/create', timeout = 5)

		if response.status_code == 200:
			return int(response.text)
	except Exception:
		pass
	return 0
