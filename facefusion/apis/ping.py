from typing import Optional

from starlette.datastructures import Headers
from starlette.websockets import WebSocket, WebSocketDisconnect


async def websocket_ping(websocket: WebSocket) -> None:
    subprotocol = get_requested_subprotocol(websocket)
    await websocket.accept(subprotocol=subprotocol)

    try:
        while True:
            await websocket.receive()

    except (WebSocketDisconnect, Exception):
        pass


def get_requested_subprotocol(websocket: WebSocket) -> Optional[str]:
    headers = Headers(scope=websocket.scope)
    protocol_header = headers.get('Sec-WebSocket-Protocol')

    if protocol_header:
        protocol, _, _ = protocol_header.partition(',')
        return protocol.strip()

    return None

