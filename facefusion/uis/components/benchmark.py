from typing import Any, Generator, List, Optional

import gradio

from facefusion import benchmarker, state_manager, translator
from facefusion.locals import LOCALS


translator.load(LOCALS, __name__)

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
		value = translator.get('uis.start_button', __name__),
		variant = 'primary',
		size = 'sm'
	)


def listen() -> None:
	BENCHMARK_START_BUTTON.click(start, outputs = BENCHMARK_BENCHMARKS_DATAFRAME)


def start() -> Generator[List[Any], None, None]:
	state_manager.sync_state()

	for benchmark in benchmarker.run():
		yield [ list(benchmark_set.values()) for benchmark_set in benchmark ]
