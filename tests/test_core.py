import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from facefusion import process_manager, state_manager
from facefusion.core import common_pre_check, conditional_process, pre_check, processors_pre_check, route, route_job_manager, route_job_runner
from facefusion.download import conditional_download
from facefusion.filesystem import copy_file, create_directory
from facefusion.jobs.job_manager import clear_jobs, find_job_ids, get_steps, init_jobs
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_path, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('download_scope', 'lite')
	state_manager.init_item('processors', [])
	state_manager.init_item('api_host', '127.0.0.1')
	state_manager.init_item('api_port', 8000)

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	with open(get_test_example_file('facefusion-invalid.ini'), 'w') as config_file:
		config_file.write('[workflow]' + os.linesep + 'workflow_mode = invalid' + os.linesep)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(state_manager.get_jobs_path())

	prepare_test_output_directory()


def test_cli() -> None:
	commands = [ sys.executable, 'facefusion.py' ]

	assert subprocess.run(commands, capture_output = True).stdout.decode().startswith('usage: facefusion.py') is True

	commands = [ sys.executable, 'facefusion.py', 'run', '--config-path', get_test_example_file('facefusion-invalid.ini') ]

	assert subprocess.run(commands).returncode == 2

	environment = os.environ.copy()
	environment['PATH'] = ''
	commands = [ sys.executable, 'facefusion.py', 'job-list', 'drafted', '--jobs-path', get_test_jobs_directory() ]

	assert subprocess.run(commands, env = environment).returncode == 2


def test_route() -> None:
	state_manager.set_item('command', 'force-download')

	with patch('facefusion.core.conditional_download_hashes', return_value = False):
		with pytest.raises(SystemExit) as system_exit:
			route({})

	assert system_exit.value.code == 1

	state_manager.set_item('command', 'benchmark')

	with patch('facefusion.benchmarker.pre_check', return_value = False):
		with pytest.raises(SystemExit) as system_exit:
			route({})

	assert system_exit.value.code == 2

	with patch('facefusion.benchmarker.render') as benchmarker_mock:
		route({})

	assert benchmarker_mock.call_count == 1

	state_manager.set_item('command', 'api')

	with patch('facefusion.apis.core.pre_check', return_value = False):
		with pytest.raises(SystemExit) as system_exit:
			route({})

	assert system_exit.value.code == 2

	with patch('facefusion.apis.core.pre_check', return_value = True):
		with patch('uvicorn.run') as uvicorn_mock:
			with pytest.raises(SystemExit) as system_exit:
				route({})

	assert uvicorn_mock.call_args.kwargs == { 'host': '127.0.0.1', 'port': 8000 }
	assert system_exit.value.code == 1

	clear_jobs(get_test_jobs_directory())
	create_directory(state_manager.get_jobs_path())
	copy_file(get_test_example_file('source.jpg'), os.path.join(state_manager.get_jobs_path(), 'drafted'))

	for command in [ 'api', 'job-list', 'run', 'batch-run', 'job-run' ]:
		state_manager.set_item('command', command)

		with patch('facefusion.apis.core.pre_check', return_value = True):
			with pytest.raises(SystemExit) as system_exit:
				route({})

		assert system_exit.value.code == 1


def test_pre_check() -> None:
	assert pre_check() is True

	with patch('sys.version_info', (3, 9, 0)):
		assert pre_check() is False

	with patch('shutil.which', return_value = None):
		assert pre_check() is False


def test_common_pre_check() -> None:
	assert common_pre_check() is True

	with patch('inspect.getsource', return_value = 'invalid'):
		assert common_pre_check() is False


def test_processors_pre_check() -> None:
	state_manager.set_item('processors', [ 'face_debugger' ])

	with patch('facefusion.processors.modules.face_debugger.core.pre_check', return_value = True):
		assert processors_pre_check() is True

	with patch('facefusion.processors.modules.face_debugger.core.pre_check', return_value = False):
		assert processors_pre_check() is False

	state_manager.set_item('processors', [])


def test_force_download() -> None:
	state_manager.set_item('command', 'force-download')

	with patch('facefusion.core.conditional_download_hashes', return_value = True):
		with patch('facefusion.core.conditional_download_sources', return_value = True) as download_mock:
			with pytest.raises(SystemExit) as system_exit:
				route({})

	assert download_mock.call_count > 1
	assert system_exit.value.code == 0

	with patch('facefusion.core.conditional_download_hashes', return_value = True):
		with patch('facefusion.core.conditional_download_sources', return_value = False) as download_mock:
			with pytest.raises(SystemExit) as system_exit:
				route({})

	assert download_mock.call_count == 1
	assert system_exit.value.code == 1


def test_route_job_manager() -> None:
	state_manager.set_item('command', 'invalid')

	assert route_job_manager({}) == 1


def test_route_job_runner() -> None:
	state_manager.set_item('command', 'invalid')

	assert route_job_runner() == 2


def test_process_headless() -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', 'invalid', '-o', get_test_output_path('test-process-headless.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert len(find_job_ids('failed')) == 1


def test_process_batch() -> None:
	commands = [ sys.executable, 'facefusion.py', 'batch-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('source.jpg'), '-o', get_test_output_path('test-process-batch-{invalid}.jpg') ]

	assert subprocess.run(commands).returncode == 1

	job_id = find_job_ids('drafted')[0]

	assert get_steps(job_id) == []

	commands = [ sys.executable, 'facefusion.py', 'batch-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('source.jpg'), '-o', get_test_output_path('test-process-batch-{invalid}.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert len(find_job_ids('drafted')) == 2

	commands = [ sys.executable, 'facefusion.py', 'batch-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('invalid-*.jpg'), '-o', get_test_output_path('test-process-batch-{index}.jpg') ]

	assert subprocess.run(commands).returncode == 1
	assert len(find_job_ids('drafted')) == 3
	assert find_job_ids('queued') == []


def test_conditional_process() -> None:
	state_manager.set_item('processors', [ 'face_debugger' ])
	state_manager.set_item('target_path', get_test_example_file('source.jpg'))
	state_manager.set_item('output_path', get_test_output_path('test-conditional-process.jpg'))
	state_manager.set_item('workflow_mode', 'image-to-video')

	assert conditional_process() == 2

	state_manager.set_item('target_path', 'invalid')
	state_manager.set_item('workflow_mode', 'auto')

	assert conditional_process() == 2
	assert state_manager.get_item('workflow_mode') == 'image-to-image'

	state_manager.set_item('processors', [])
