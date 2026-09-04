import pytest

from facefusion import state_manager
from facefusion.session_context import set_session_id


@pytest.fixture(scope = 'session', autouse = True)
def before_session() -> None:
	set_session_id('test')
	state_manager.init_state('test')
