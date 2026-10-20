import asyncio
from typing import List

from facefusion import store_creator
from facefusion.session_manager import resolve_owner_id
from facefusion.types import HttpChannel, HttpTask, SessionHttp, SessionHttpSet, SessionId, Store

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


def start_request(channel : HttpChannel, task : HttpTask) -> None:
	owner_id = resolve_owner_id()

	if store_creator.has_content(HTTP_STORE, owner_id):
		store_creator.get_content(HTTP_STORE, owner_id).setdefault(channel, []).append(
		{
			'task': task,
			'event_loop': asyncio.get_running_loop()
		})


def end_request(channel : HttpChannel, task : HttpTask) -> None:
	owner_id = resolve_owner_id()
	session_http_set : SessionHttpSet = store_creator.get_content(HTTP_STORE, owner_id)

	if session_http_set and channel in session_http_set:
		sessions : List[SessionHttp] = []

		for session_http in session_http_set.get(channel):
			if not session_http.get('task') == task:
				sessions.append(session_http)

		del session_http_set[channel]

		if sessions:
			session_http_set[channel] = sessions


def destroy(session_id : SessionId) -> None:
	session_http_set : SessionHttpSet = store_creator.get_content(HTTP_STORE, session_id)
	store_creator.delete_content(HTTP_STORE, session_id)

	if session_http_set:
		for sessions in session_http_set.values():
			for session_http in sessions:
				task = session_http.get('task')

				if task._state == 'PENDING':
					session_http.get('event_loop').call_soon_threadsafe(task.cancel)
