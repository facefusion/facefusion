from typing import Any, Generator, List, Optional

import gradio

from facefusion import benchmarker, state_manager, wording
from facefusion.types import BenchmarkResolution
from facefusion.uis.core import get_ui_component

BENCHMARK_BENCHMARKS_DATAFRAME : Optional[gradio.Dataframe] = None
BENCHMARK_START_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global BENCHMARK_BENCHMARKS_DATAFRAME
	global BENCHMARK_START_BUTTON

	BENCHMARK_BENCHMARKS_DATAFRAME = gradio.Dataframe(
		headers =
		[
			'target_path',
			'cycle_count',
			'average_run',
			'fastest_run',
			'slowest_run',
			'relative_fps'
		],
		datatype =
		[
			'str',
			'number',
			'number',
			'number',
			'number',
			'number'
		],
		show_label = False
	)
	BENCHMARK_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)


def listen() -> None:
	benchmark_resolutions_checkbox_group = get_ui_component('benchmark_resolutions_checkbox_group')
	benchmark_cycle_count_slider = get_ui_component('benchmark_cycle_count_slider')

	if benchmark_resolutions_checkbox_group and benchmark_cycle_count_slider:
		BENCHMARK_START_BUTTON.click(start, inputs = [ benchmark_resolutions_checkbox_group, benchmark_cycle_count_slider ], outputs = BENCHMARK_BENCHMARKS_DATAFRAME)


def start(benchmark_resolutions : List[BenchmarkResolution], benchmark_cycle_count : int) -> Generator[List[Any], None, None]:
	state_manager.set_item('benchmark_resolutions', benchmark_resolutions)
	state_manager.set_item('benchmark_cycle_count', benchmark_cycle_count)
	state_manager.sync_item('execution_providers')
	state_manager.sync_item('execution_thread_count')
	state_manager.sync_item('execution_queue_count')

	for benchmark in benchmarker.run():
		yield [ list(benchmark_set.values()) for benchmark_set in benchmark ]
