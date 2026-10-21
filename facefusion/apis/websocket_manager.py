import asyncio
from typing import List

from starlette.websockets import WebSocketState

from facefusion import store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import SessionId, SessionWebsocket, SessionWebsocketSet, Store, Websocket, WebsocketChannel

WEBSOCKET_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(WEBSOCKET_STORE, owner_id)


def has_connection(channel : WebsocketChannel) -> bool:
	owner_id = resolve_owner_id()
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, owner_id)

	if session_websocket_set:
		return channel in session_websocket_set

	return False


def start_connection(channel : WebsocketChannel, websocket : Websocket) -> None:
	owner_id = resolve_owner_id()

	if store_creator.has_content(WEBSOCKET_STORE, owner_id):
		store_creator.get_content(WEBSOCKET_STORE, owner_id).setdefault(channel, []).append(
		{
			'websocket': websocket,
			'event_loop': asyncio.get_running_loop()
		})


def end_connection(channel : WebsocketChannel, websocket : Websocket) -> None:
	owner_id = resolve_owner_id()
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, owner_id)

	if session_websocket_set and channel in session_websocket_set:
		sessions : List[SessionWebsocket] = []

		for session_websocket in session_websocket_set.get(channel):
			if not session_websocket.get('websocket') == websocket:
				sessions.append(session_websocket)

		del session_websocket_set[channel]

		if sessions:
			session_websocket_set[channel] = sessions


def destroy(session_id : SessionId) -> None:
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, session_id)
	store_creator.delete_content(WEBSOCKET_STORE, session_id)

	if session_websocket_set:
		for sessions in session_websocket_set.values():
			for session_websocket in sessions:
				websocket = session_websocket.get('websocket')

				if websocket.application_state == WebSocketState.CONNECTED:
					asyncio.run_coroutine_threadsafe(websocket.close(), session_websocket.get('event_loop')).result()
