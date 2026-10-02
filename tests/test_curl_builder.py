from shutil import which

from facefusion import metadata
from facefusion.curl_builder import chain, download, ping, run, set_retry, set_timeout


def test_run() -> None:
	user_agent = metadata.get('name') + '/' + metadata.get('version')

	assert run([]) == [ which('curl'), '--user-agent', user_agent, '--location', '--silent', '--ssl-no-revoke' ]


def test_chain() -> None:
	assert chain(
		ping(metadata.get('url')),
		set_timeout(5)
	) == [ '-I', metadata.get('url'), '--connect-timeout', '5' ]


def test_ping() -> None:
	assert ping(metadata.get('url')) == [ '-I', metadata.get('url') ]


def test_download() -> None:
	assert download(metadata.get('url'), 'source.jpg') == [ '--create-dirs', '--continue-at', '-', '--output', 'source.jpg', metadata.get('url') ]


def test_set_timeout() -> None:
	assert set_timeout(5) == [ '--connect-timeout', '5' ]


def test_set_retry() -> None:
	assert set_retry(5) == [ '--retry', '5' ]
