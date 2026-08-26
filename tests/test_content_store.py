import pytest

from facefusion.content_store import clear, get_hit, get_rate, set_hit, tick


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear()


def test_get_hit() -> None:
	assert get_hit() == 0

	set_hit()

	assert get_hit() == 1


def test_set_hit() -> None:
	set_hit()
	set_hit()

	assert get_hit() == 2


def test_get_rate() -> None:
	assert get_rate() == 0.0

	for _ in range(100):
		tick()

	set_hit()

	assert get_rate() == 30.0


def test_clear() -> None:
	tick()
	set_hit()
	clear()

	assert get_hit() == 0
	assert get_rate() == 0.0
