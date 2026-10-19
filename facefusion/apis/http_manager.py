import asyncio

from facefusion import store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import HttpChannel, SessionHttpSet, SessionId, Store

HTTP_STORE : Store = store_creator.create_store({})


def init() -> None:
	owner_id = resolve_owner_id()
	store_creator.init_content(HTTP_STORE, owner_id)


def has_request(channel : HttpChannel) -> bool:
	owner_id = resolve_owner_id()
	session_http_set : SessionHttpSet = store_creator.get_content(HTTP_STORE, owner_id)

	if session_http_set:
		return channel in session_http_set

	return False


def start_request(channel : HttpChannel) -> None:
	owner_id = resolve_owner_id()

	if store_creator.has_content(HTTP_STORE, owner_id):
		store_creator.get_content(HTTP_STORE, owner_id)[channel] =\
		{
			'task': asyncio.current_task(),
			'event_loop': asyncio.get_running_loop()
		}


def end_request(channel : HttpChannel) -> None:
	owner_id = resolve_owner_id()
	session_http_set : SessionHttpSet = store_creator.get_content(HTTP_STORE, owner_id)

	if session_http_set and channel in session_http_set:
		del session_http_set[channel]


def destroy(session_id : SessionId) -> None:
	session_http_set : SessionHttpSet = store_creator.get_content(HTTP_STORE, session_id)
	store_creator.delete_content(HTTP_STORE, session_id)

	if session_http_set:
		for session_http in session_http_set.values():
			task = session_http.get('task')

			if task._state == 'PENDING':
				session_http.get('event_loop').call_soon_threadsafe(task.cancel)
