from facefusion.types import ContentSet

CONTENT_STORE : ContentSet =\
{
	'hit': 0,
	'total': 0
}


def count_hit() -> None:
	CONTENT_STORE['hit'] += 1


def count_total() -> None:
	CONTENT_STORE['total'] += 1


def get_hit() -> int:
	return CONTENT_STORE.get('hit')


def get_total() -> int:
	return CONTENT_STORE.get('total')


def get_rate() -> float:
	if CONTENT_STORE.get('hit') and CONTENT_STORE.get('total'):
		return CONTENT_STORE.get('hit') / CONTENT_STORE.get('total') * 100
	return 0.0


def clear() -> None:
	CONTENT_STORE['hit'] = 0
	CONTENT_STORE['total'] = 0
