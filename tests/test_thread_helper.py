from typing import Iterator

import pytest

from facefusion.session_context import get_session_id, resolve_local_id, set_session_id
from facefusion.thread_helper import create_executor


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = resolve_local_id()

	set_session_id('session-a')

	yield

	set_session_id(local_id)


def test_create_executor() -> None:
	with create_executor(1) as executor:
		assert executor.submit(get_session_id).result() == 'session-a'
