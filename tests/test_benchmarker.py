import hashlib
import os
import tempfile
from unittest.mock import patch

import pytest
from _pytest.logging import LogCaptureFixture

from facefusion import state_manager
from facefusion.benchmarker import cycle, pre_check, render, run, suggest_output_path


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('benchmark_mode', 'warm')
	state_manager.init_item('benchmark_resolutions', [ '240p', '360p' ])
	state_manager.init_item('benchmark_cycle_count', 2)

	pre_check()


def test_pre_check() -> None:
	assert pre_check() is True


def test_run() -> None:
	with patch('facefusion.core.conditional_process', return_value = 0) as core_mock:
		benchmarks = list(run())

	assert len(benchmarks) == 2
	assert [ benchmark_set.get('target_path') for benchmark_set in benchmarks[-1] ] == [ '.assets/examples/target-240p.mp4', '.assets/examples/target-360p.mp4' ]
	assert core_mock.call_count == 6
	assert state_manager.get_item('source_paths') == [ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ]
	assert state_manager.get_item('target_path') == '.assets/examples/target-360p.mp4'
	assert state_manager.get_item('output_path') == suggest_output_path('.assets/examples/target-360p.mp4')
	assert state_manager.get_item('temp_frame_format') == 'bmp'
	assert state_manager.get_item('video_memory_strategy') == 'tolerant'


def test_cycle() -> None:
	state_manager.init_item('target_path', '.assets/examples/target-240p.mp4')

	with patch('facefusion.core.conditional_process', return_value = 0) as core_mock:
		benchmark_set = cycle(3)

	assert benchmark_set.get('target_path') == '.assets/examples/target-240p.mp4'
	assert benchmark_set.get('cycle_count') == 3
	assert sorted([ benchmark_set.get('slowest_run'), benchmark_set.get('average_run'), benchmark_set.get('fastest_run') ]) == [ benchmark_set.get('fastest_run'), benchmark_set.get('average_run'), benchmark_set.get('slowest_run') ]
	assert benchmark_set.get('relative_fps') > 0
	assert core_mock.call_count == 4
	assert state_manager.get_item('output_video_fps') == 25.0

	state_manager.init_item('benchmark_mode', 'cold')

	with patch('facefusion.core.conditional_process', return_value = 0) as core_mock:
		with patch('facefusion.face_store.clear') as face_store_mock:
			cycle(3)

	assert core_mock.call_count == 3
	assert face_store_mock.call_count == 3

	state_manager.init_item('benchmark_mode', 'warm')


def test_suggest_output_path() -> None:
	assert suggest_output_path('.assets/examples/target-240p.mp4') == os.path.join(tempfile.gettempdir(), hashlib.sha1('.assets/examples/target-240p.mp4'.encode()).hexdigest() + '.mp4')
	assert suggest_output_path('target-240p.jpg').endswith('.jpg') is True


def test_render(caplog : LogCaptureFixture) -> None:
	state_manager.init_item('benchmark_resolutions', [ '240p', 'invalid' ])

	with patch('facefusion.core.conditional_process', return_value = 0):
		render()

	assert caplog.messages[1].split() == [ '|', 'target_path', '|', 'cycle_count', '|', 'average_run', '|', 'fastest_run', '|', 'slowest_run', '|', 'relative_fps', '|' ]
	assert caplog.messages[3].split()[1] == '.assets/examples/target-240p.mp4'
	assert caplog.messages[3].split()[3] == '2'
	assert len(caplog.messages) == 5
