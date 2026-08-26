from facefusion.types import ContentSet

CONTENT_STORE : ContentSet =\
{
	'hit': 0,
	'total': 0
}


def tick(step : int = 30) -> bool:
	CONTENT_STORE['total'] += 1

	return CONTENT_STORE.get('total') % step == 0


def get_hit() -> int:
	return CONTENT_STORE.get('hit')


def set_hit() -> None:
	CONTENT_STORE['hit'] += 1


def get_rate(step : int = 30) -> float:
	if CONTENT_STORE.get('hit') and CONTENT_STORE.get('total'):
		return CONTENT_STORE.get('hit') / CONTENT_STORE.get('total') * step * 100
	return 0.0


def clear() -> None:
	CONTENT_STORE['hit'] = 0
	CONTENT_STORE['total'] = 0
