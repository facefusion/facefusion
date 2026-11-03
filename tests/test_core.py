import signal
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from facefusion import content_store, core, process_manager, session_context, session_manager, state_manager, store_creator, video_manager
from facefusion.apis.core import stop_server
from facefusion.types import ErrorCode
from tests.assert_helper import get_test_example_file, get_test_output_path


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	local_id = session_context.resolve_local_id()
	session_context.set_session_id(local_id)


def test_route(mocker : MockerFixture) -> None:
	server_mock = Mock()
	server_mock.should_exit = True
	state_manager.set_item('command', 'api')
	state_manager.set_item('jobs_path', get_test_output_path('jobs'))

	mocker.patch('facefusion.core.common_pre_check', return_value = True)
	mocker.patch('facefusion.core.processors_pre_check', return_value = True)
	mocker.patch('facefusion.apis.core.pre_check', return_value = True)
	mocker.patch('facefusion.core.job_manager.init_jobs', return_value = True)
	mocker.patch('facefusion.apis.core.create_server', return_value = server_mock)

	signal_mock = mocker.patch('facefusion.core.signal.signal')
	graceful_exit_mock = mocker.patch('facefusion.core.graceful_exit', side_effect = SystemExit)
	hard_exit_mock = mocker.patch('facefusion.core.hard_exit', side_effect = SystemExit)

	with pytest.raises(SystemExit):
		core.route({})

	sigint_call, sigterm_call = signal_mock.call_args_list

	assert sigint_call.args[0] == signal.SIGINT
	assert sigint_call.args[1].func is stop_server
	assert sigterm_call.args[0] == signal.SIGTERM
	assert sigterm_call.args[1].func is stop_server
	assert server_mock.run.call_count == 1

	graceful_exit_mock.assert_called_once_with(0)

	assert hard_exit_mock.call_count == 0

	server_mock.should_exit = False

	with pytest.raises(SystemExit):
		core.route({})

	hard_exit_mock.assert_called_once_with(1)

	state_manager.clear_item('command')
	state_manager.clear_item('jobs_path')


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
	mocker.patch('facefusion.core.common_pre_check', return_value = True)
	mocker.patch('facefusion.core.processors_pre_check', return_value = True)

	conditional_process_mock = mocker.patch('facefusion.core.conditional_process', return_value = error_code)
	fork_session_mock = mocker.spy(session_manager, 'fork_session')
	start_mock = mocker.spy(process_manager, 'start')
	end_process_mock = mocker.spy(process_manager, 'end_process')

	assert core.process_step('job-id', 0, step_args) == error_code

	conditional_process_mock.assert_called_once_with()

	assert start_mock.call_count == 1
	assert end_process_mock.call_count == 1

	assert session_manager.has_fork_session(local_id) is False

	fork_id = fork_session_mock.spy_return
	stores = [ state_manager.STATE_SET, content_store.CONTENT_STORE, process_manager.PROCESS_STORE, video_manager.VIDEO_POOL_STORE ]

	for store in stores:
		assert store_creator.has_content(store, fork_id) is False
