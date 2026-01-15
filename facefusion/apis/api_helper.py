from typing import Optional

from starlette.datastructures import Headers
from starlette.types import Scope


def get_sec_websocket_protocol(scope : Scope) -> Optional[str]:
	protocol_header = Headers(scope = scope).get('Sec-WebSocket-Protocol')

	if protocol_header:
		protocol, _, _ = protocol_header.partition(',')
		return protocol.strip()

	return None
