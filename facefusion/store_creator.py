from copy import deepcopy
from typing import List

from facefusion.types import SessionId, Store, StoreContent


def create_store(content : StoreContent) -> Store:
	store : Store =\
	{
		'__init__': content,
		'content_set': {}
	}

	return store


def init_content(store : Store, session_id : SessionId) -> None:
	store['content_set'][session_id] = deepcopy(store.get('__init__'))


def has_content(store : Store, session_id : SessionId) -> bool:
	return session_id in store.get('content_set')


def get_content(store : Store, session_id : SessionId) -> StoreContent:
	return store.get('content_set').get(session_id)


def set_content(store : Store, session_id : SessionId, content : StoreContent) -> None:
	store['content_set'][session_id] = content


def delete_content(store : Store, session_id : SessionId) -> None:
	if has_content(store, session_id):
		del store['content_set'][session_id]


def delete_contents(store : Store, session_ids : List[SessionId]) -> None:
	for session_id in session_ids:
		delete_content(store, session_id)
