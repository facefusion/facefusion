from argparse import ArgumentParser
from typing import cast

import pytest

from facefusion import capability_store, state_manager
from facefusion.args_helper import apply_args, extract_api_args, extract_cli_args, extract_step_args, extract_sys_args, filter_api_step_args, filter_cli_step_args
from facefusion.types import State


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	program = ArgumentParser()

	state_manager.init()

	capability_store.register_capability_set(
		[
			program.add_argument('--workflow-mode', default = 'auto'),
			program.add_argument('--workflow-strategy', default = 'memory')
		],
		scopes = [ 'api', 'cli' ],
		groups = [ 'workflow' ]
	)
	capability_store.register_capability_set(
		[
			program.add_argument('--video-memory-strategy', default = 'strict')
		],
		scopes = [ 'cli', 'sys' ],
		groups = [ 'memory' ]
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	state_manager.clear()


def test_apply_args() -> None:
	apply_args({ 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' }, state_manager.init_item)

	assert state_manager.get_item('workflow_mode') == 'auto'
	assert state_manager.get_item('workflow_strategy') == 'memory'
	assert state_manager.get_item('video_memory_strategy') == 'strict'


def test_extract_api_args() -> None:
	state = cast(State, { 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' })

	assert extract_api_args(state) == { 'workflow_mode': 'auto', 'workflow_strategy': 'memory' }


def test_extract_cli_args() -> None:
	state = cast(State, { 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' })

	assert extract_cli_args(state) == { 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' }


def test_extract_sys_args() -> None:
	state = cast(State, { 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' })

	assert extract_sys_args(state) == { 'video_memory_strategy': 'strict' }


def test_extract_step_args() -> None:
	state = cast(State, { 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' })

	assert extract_step_args(state) == { 'workflow_mode': 'auto', 'workflow_strategy': 'memory' }


def test_filter_api_step_args() -> None:
	assert filter_api_step_args({ 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' }) == { 'workflow_mode': 'auto', 'workflow_strategy': 'memory' }


def test_filter_cli_step_args() -> None:
	assert filter_cli_step_args({ 'workflow_mode': 'auto', 'workflow_strategy': 'memory', 'video_memory_strategy': 'strict' }) == { 'workflow_mode': 'auto', 'workflow_strategy': 'memory' }
