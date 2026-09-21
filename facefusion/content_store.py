from facefusion import store_creator
from facefusion.session_context import get_session_id
from facefusion.types import SessionId, Store

CONTENT_STORE : Store = store_creator.create_store(
{
	'hit': 0,
	'total': 0
})


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(CONTENT_STORE, session_id)


def tick(step : int = 30) -> bool:
	session_id = get_session_id()
	content_set = store_creator.get_content(CONTENT_STORE, session_id)
	content_set['total'] += 1

	return content_set.get('total') % step == 0


def get_hit() -> int:
	session_id = get_session_id()
	content_set = store_creator.get_content(CONTENT_STORE, session_id)

	return content_set.get('hit')


def set_hit() -> None:
	session_id = get_session_id()
	content_set = store_creator.get_content(CONTENT_STORE, session_id)
	content_set['hit'] += 1


def calculate_rate(step : int = 30) -> float:
	session_id = get_session_id()
	content_set = store_creator.get_content(CONTENT_STORE, session_id)

	if content_set.get('hit') and content_set.get('total'):
		return content_set.get('hit') / content_set.get('total') * step * 100
	return 0.0


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(CONTENT_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(CONTENT_STORE, session_id)

