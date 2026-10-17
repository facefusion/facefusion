import pytest
from pytest_mock import MockerFixture

from facefusion import content_store, core, process_manager, session_context, session_manager, state_manager, store_creator, video_manager
from facefusion.types import ErrorCode
from tests.assert_helper import get_test_example_file, get_test_output_path


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	local_id = session_context.resolve_local_id()
	session_context.set_session_id(local_id)


@pytest.mark.parametrize('error_code', [ 0, 1, 2, 3, 4 ])
def test_process_step(mocker : MockerFixture, error_code : ErrorCode) -> None:
	local_id = session_context.resolve_local_id()
	step_args =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output.mp4')
	}

	mocker.patch('facefusion.core.job_manager.count_step_total', return_value = 1)
	mocker.patch('facefusion.core.session_manager.observe_cli_session')
	mocker.patch('facefusion.core.store_manager.observe_cli_session')
	mocker.patch('facefusion.core.apply_args')
	mocker.patch('facefusion.core.common_pre_check', return_value = True)
	mocker.patch('facefusion.core.processors_pre_check', return_value = True)
	conditional_process_mock = mocker.patch('facefusion.core.conditional_process', return_value = error_code)
	fork_session_mock = mocker.spy(session_manager, 'fork_session')

	assert core.process_step('job-id', 0, step_args) == error_code

	conditional_process_mock.assert_called_once_with()

	assert session_manager.has_fork_session(local_id) is False

	fork_id = fork_session_mock.spy_return
	stores = [ state_manager.STATE_SET, content_store.CONTENT_STORE, process_manager.PROCESS_STORE, video_manager.VIDEO_POOL_STORE ]

	for store in stores:
		assert store_creator.has_content(store, fork_id) is False
