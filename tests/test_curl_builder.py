from shutil import which

from facefusion import curl_builder, metadata


def test_run() -> None:
	user_agent = metadata.get('name') + '/' + metadata.get('version')

	assert curl_builder.run([]) == [ which('curl'), '--user-agent', user_agent, '--insecure', '--location', '--silent' ]


def test_chain() -> None:
	commands = curl_builder.chain(
		curl_builder.head(metadata.get('url'))
	)

	assert commands == [ '-I', metadata.get('url') ]
