from facefusion.apis.api_helper import get_sec_websocket_protocol


def test_get_sec_websocket_protocol() -> None:
	scope =\
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'access_token.abc') ]
	}

	assert get_sec_websocket_protocol(scope) == 'access_token.abc'
