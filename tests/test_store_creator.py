from facefusion.store_creator import create_store, delete_content, get_content, has_content, init_content, set_content


def test_create_store() -> None:
	store = create_store({ 'total': 0 })

	assert store.get('__init__') == { 'total': 0 }
	assert store.get('content_set') == {}


def test_init_content() -> None:
	store = create_store({ 'total': 0 })

	init_content(store, 'session-a')

	assert store.get('content_set').get('session-a') == { 'total': 0 }
	assert not store.get('content_set').get('session-a') == store.get('__init__') is False


def test_has_content() -> None:
	store = create_store({ 'total': 0 })

	assert has_content(store, 'session-a') is False

	init_content(store, 'session-a')

	assert has_content(store, 'session-a') is True
	assert has_content(store, 'session-b') is False


def test_get_content() -> None:
	store = create_store({ 'total': 0 })

	init_content(store, 'session-a')

	assert get_content(store, 'session-a') == { 'total': 0 }
	assert get_content(store, 'session-b') is None

	get_content(store, 'session-a')['total'] += 1

	assert get_content(store, 'session-a') == { 'total': 1 }


def test_set_content() -> None:
	store = create_store({ 'total': 0 })

	set_content(store, 'session-a', { 'total': 3 })

	assert get_content(store, 'session-a') == { 'total': 3 }
	assert has_content(store, 'session-b') is False


def test_delete_content() -> None:
	store = create_store({ 'total': 0 })

	init_content(store, 'session-a')
	init_content(store, 'session-b')
	delete_content(store, 'session-a')

	assert list(store.get('content_set').keys()) == [ 'session-b' ]

	delete_content(store, 'session-a')

	assert list(store.get('content_set').keys()) == [ 'session-b' ]

