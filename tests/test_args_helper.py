from argparse import ArgumentParser

import pytest

from facefusion import capability_store, state_manager
from facefusion.args_helper import apply_args, extract_api_args, extract_cli_args, extract_step_args, extract_sys_args, filter_api_step_args, filter_cli_step_args
from facefusion.download import conditional_download
from facefusion.types import Args, State
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	program = ArgumentParser()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	state_manager.init()

	capability_store.register_capability_set(
		[
			program.add_argument(
				'--workflow-mode',
				default = 'auto'
			)
		],
		scopes = [ 'api', 'cli' ],
		groups = [ 'workflow' ]
	)
	capability_store.register_capability_set(
		[
			program.add_argument(
				'--temp-path'
			)
		],
		scopes = [ 'cli' ],
		groups = [ 'paths' ]
	)
	capability_store.register_capability_set(
		[
			program.add_argument(
				'--video-memory-strategy',
				default = 'strict'
			)
		],
		scopes = [ 'cli', 'sys' ],
		groups = [ 'memory' ]
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.clear()


def create_state() -> State:
	state : State =\
	{
		'workflow_mode': 'auto',
		'temp_path': '.temp',
		'video_memory_strategy': 'strict',
		'invalid': 'invalid'
	} #type:ignore[typeddict-item, typeddict-unknown-key]

	return state


def create_args() -> Args:
	args : Args =\
	{
		'workflow_mode': 'auto',
		'temp_path': '.temp',
		'video_memory_strategy': 'strict',
		'invalid': 'invalid'
	}

	return args


def test_apply_args() -> None:
	args : Args =\
	{
		'target_path': get_test_example_file('target-240p.mp4'),
		'face_detector_margin': [ 10 ],
		'face_mask_padding': [ 1, 2 ],
		'output_audio_fps': 120,
		'processors': [ 'face_swapper' ],
		'face_swapper_model': 'hyperswap_1a_256'
	}

	apply_args(args, state_manager.init_item)

	assert state_manager.get_item('target_path') == get_test_example_file('target-240p.mp4')
	assert state_manager.get_item('face_detector_margin') == (10, 10, 10, 10)
	assert state_manager.get_item('face_mask_padding') == (1, 2, 1, 2)
	assert state_manager.get_item('output_audio_fps') == 60.0
	assert state_manager.get_item('output_video_fps') == 25.0
	assert state_manager.get_item('processors') == [ 'face_swapper' ]
	assert state_manager.get_item('face_swapper_model') == 'hyperswap_1a_256'

	state_manager.clear()
	args =\
	{
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_video_fps': 30.0
	}

	apply_args(args, state_manager.init_item)

	assert state_manager.get_item('output_video_fps') == 30.0

	state_manager.clear()
	args =\
	{
		'target_path': get_test_example_file('source.jpg'),
		'output_video_fps': 30.0
	}

	apply_args(args, state_manager.init_item)

	assert state_manager.get_item('output_video_fps') == 30.0

	args =\
	{
		'target_path': get_test_example_file('source.jpg')
	}

	apply_args(args, state_manager.init_item)

	assert state_manager.get_item('output_video_fps') == 30.0
	assert state_manager.get_item('target_path') == get_test_example_file('source.jpg')

	state_manager.clear()
	args = {}

	for key in State.__annotations__:
		if key not in [ 'config_path', 'api_key', 'face_detector_margin', 'face_mask_padding', 'output_audio_fps', 'output_video_fps' ]:
			args[key] = key

	apply_args(args, state_manager.init_item)

	for key in args:
		assert state_manager.get_item(key) == key


def test_extract_api_args() -> None:
	assert extract_api_args(create_state()) ==\
	{
		'workflow_mode': 'auto'
	}
	assert extract_api_args(state_manager.get_state()) == {}


def test_extract_cli_args() -> None:
	assert extract_cli_args(create_state()) ==\
	{
		'workflow_mode': 'auto',
		'temp_path': '.temp',
		'video_memory_strategy': 'strict'
	}
	assert extract_cli_args(state_manager.get_state()) == {}


def test_extract_sys_args() -> None:
	assert extract_sys_args(create_state()) ==\
	{
		'video_memory_strategy': 'strict'
	}
	assert extract_sys_args(state_manager.get_state()) == {}


def test_extract_step_args() -> None:
	assert extract_step_args(create_state()) ==\
	{
		'workflow_mode': 'auto',
		'temp_path': '.temp'
	}
	assert extract_step_args(state_manager.get_state()) == {}


def test_filter_api_step_args() -> None:
	assert filter_api_step_args(create_args()) ==\
	{
		'workflow_mode': 'auto'
	}
	assert filter_api_step_args({}) == {}


def test_filter_cli_step_args() -> None:
	assert filter_cli_step_args(create_args()) ==\
	{
		'workflow_mode': 'auto',
		'temp_path': '.temp'
	}
	assert filter_cli_step_args({}) == {}
