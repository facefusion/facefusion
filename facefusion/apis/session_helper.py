from typing import Optional

from starlette.datastructures import Headers
from starlette.types import Scope

from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.types import Token


def extract_access_token(scope : Scope) -> Optional[Token]:
	if scope.get('type') == 'http':
		auth_header = Headers(scope = scope).get('Authorization')

		if auth_header:
			auth_prefix, _, access_token = auth_header.partition(' ')

			if auth_prefix.lower() == 'bearer' and access_token:
				return access_token

	if scope.get('type') == 'websocket':
		subprotocol = get_sec_websocket_protocol(scope)

		if subprotocol:
			protocol_prefix, _, access_token = subprotocol.partition('.')

			if protocol_prefix == 'access_token' and access_token:
				return access_token

	return None
