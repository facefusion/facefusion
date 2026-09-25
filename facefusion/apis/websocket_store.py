from anyio.from_thread import run
from anyio.lowlevel import current_token

from facefusion import store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import SessionId, SessionWebsocketSet, Store, Websocket

WEBSOCKET_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(WEBSOCKET_STORE, owner_id)


def set_websocket(websocket : Websocket) -> None:
	owner_id = resolve_owner_id()

	if store_creator.has_content(WEBSOCKET_STORE, owner_id):
		store_creator.get_content(WEBSOCKET_STORE, owner_id)[id(websocket)] =\
		{
			'websocket': websocket,
			'event_loop_token': current_token()
		}


def delete_websocket(websocket : Websocket) -> None:
	owner_id = resolve_owner_id()
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, owner_id)

	if session_websocket_set and id(websocket) in session_websocket_set:
		del session_websocket_set[id(websocket)]


def destroy(session_id : SessionId) -> None:
	session_websocket_set : SessionWebsocketSet = store_creator.get_content(WEBSOCKET_STORE, session_id)
	store_creator.delete_content(WEBSOCKET_STORE, session_id)

	if session_websocket_set:
		for session_websocket in session_websocket_set.values():
			run(session_websocket.get('websocket').close, token = session_websocket.get('event_loop_token'))
