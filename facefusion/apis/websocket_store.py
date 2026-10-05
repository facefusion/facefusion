import asyncio

from starlette.websockets import WebSocketState

from facefusion import store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import SessionId, SessionWebsocketSet, Store, Websocket, WebsocketChannel

WEBSOCKET_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(WEBSOCKET_STORE, owner_id)


def has_websocket(channel : WebsocketChannel) -> bool:
	owner_id = resolve_owner_id()
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, owner_id)

	if session_websocket_set:
		return channel in session_websocket_set

	return False


def set_websocket(channel : WebsocketChannel, websocket : Websocket) -> None:
	owner_id = resolve_owner_id()

	if store_creator.has_content(WEBSOCKET_STORE, owner_id):
		store_creator.get_content(WEBSOCKET_STORE, owner_id)[channel] =\
		{
			'websocket': websocket,
			'event_loop': asyncio.get_running_loop()
		}


def delete_websocket(channel : WebsocketChannel) -> None:
	owner_id = resolve_owner_id()
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, owner_id)

	if session_websocket_set and channel in session_websocket_set:
		del session_websocket_set[channel]


def destroy(session_id : SessionId) -> None:
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, session_id)
	store_creator.delete_content(WEBSOCKET_STORE, session_id)

	if session_websocket_set:
		for session_websocket in session_websocket_set.values():
			websocket = session_websocket.get('websocket')

			if websocket.application_state == WebSocketState.CONNECTED:
				asyncio.run_coroutine_threadsafe(websocket.close(), session_websocket.get('event_loop')).result()
