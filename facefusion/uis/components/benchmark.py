from typing import Any, Optional, List, Dict, Generator
import time
import tempfile
import statistics
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.vision import count_video_frame_total
from facefusion.core import limit_resources, conditional_process
from facefusion.uis.typing import Update
from facefusion.utilities import normalize_output_path, clear_temp

BENCHMARK_RESULTS_DATAFRAME : Optional[gradio.Dataframe] = None
BENCHMARK_RUNS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None
BENCHMARK_CYCLES_SLIDER : Optional[gradio.Button] = None
BENCHMARK_START_BUTTON : Optional[gradio.Button] = None
BENCHMARK_CLEAR_BUTTON : Optional[gradio.Button] = None
BENCHMARKS : Dict[str, str] = \
{
	'240p': '.assets/examples/target-240p.mp4',
	'360p': '.assets/examples/target-360p.mp4',
	'540p': '.assets/examples/target-540p.mp4',
	'720p': '.assets/examples/target-720p.mp4',
	'1080p': '.assets/examples/target-1080p.mp4',
	'1440p': '.assets/examples/target-1440p.mp4',
	'2160p': '.assets/examples/target-2160p.mp4'
}


def render() -> None:
	global BENCHMARK_RESULTS_DATAFRAME
	global BENCHMARK_RUNS_CHECKBOX_GROUP
	global BENCHMARK_CYCLES_SLIDER
	global BENCHMARK_START_BUTTON
	global BENCHMARK_CLEAR_BUTTON

	with gradio.Box():
		BENCHMARK_RESULTS_DATAFRAME = gradio.Dataframe(
			label = wording.get('benchmark_results_dataframe_label'),
			headers =
			[
				'target_path',
				'benchmark_cycles',
				'average_run',
				'fastest_run',
				'slowest_run',
				'relative_fps'
			],
			row_count = len(BENCHMARKS),
			datatype =
			[
				'str',
				'number',
				'number',
				'number',
				'number',
				'number'
			]
		)
	with gradio.Box():
		BENCHMARK_RUNS_CHECKBOX_GROUP = gradio.CheckboxGroup(
			label = wording.get('benchmark_runs_checkbox_group_label'),
			value = list(BENCHMARKS.keys()),
			choices = list(BENCHMARKS.keys())
		)
		BENCHMARK_CYCLES_SLIDER = gradio.Slider(
			label = wording.get('benchmark_cycles_slider_label'),
			minimum = 1,
			step = 1,
			value = 3,
			maximum = 10
		)
	with gradio.Row():
		BENCHMARK_START_BUTTON = gradio.Button(wording.get('start_button_label'))
		BENCHMARK_CLEAR_BUTTON = gradio.Button(wording.get('clear_button_label'))


def listen() -> None:
	BENCHMARK_RUNS_CHECKBOX_GROUP.change(update_benchmark_runs, inputs = BENCHMARK_RUNS_CHECKBOX_GROUP, outputs = BENCHMARK_RUNS_CHECKBOX_GROUP)
	BENCHMARK_START_BUTTON.click(start, inputs = [ BENCHMARK_RUNS_CHECKBOX_GROUP, BENCHMARK_CYCLES_SLIDER ], outputs = BENCHMARK_RESULTS_DATAFRAME)
	BENCHMARK_CLEAR_BUTTON.click(clear, outputs = BENCHMARK_RESULTS_DATAFRAME)


def update_benchmark_runs(benchmark_runs : List[str]) -> Update:
	return gradio.update(value = benchmark_runs)


def start(benchmark_runs : List[str], benchmark_cycles : int) -> Generator[List[Any], None, None]:
	facefusion.globals.source_path = '.assets/examples/source.jpg'
	target_paths = [ BENCHMARKS[benchmark_run] for benchmark_run in benchmark_runs if benchmark_run in BENCHMARKS ]
	benchmark_results = []
	if target_paths:
		warm_up(BENCHMARKS['240p'])
		for target_path in target_paths:
			benchmark_results.append(benchmark(target_path, benchmark_cycles))
			yield benchmark_results


def warm_up(target_path : str) -> None:
	facefusion.globals.target_path = target_path
	facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, tempfile.gettempdir())
	conditional_process()


def benchmark(target_path : str, benchmark_cycles : int) -> List[Any]:
	process_times = []
	total_fps = 0.0
	for i in range(benchmark_cycles):
		facefusion.globals.target_path = target_path
		facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, tempfile.gettempdir())
		video_frame_total = count_video_frame_total(facefusion.globals.target_path)
		start_time = time.perf_counter()
		limit_resources()
		conditional_process()
		end_time = time.perf_counter()
		process_time = end_time - start_time
		total_fps += video_frame_total / process_time
		process_times.append(process_time)
	average_run = round(statistics.mean(process_times), 2)
	fastest_run = round(min(process_times), 2)
	slowest_run = round(max(process_times), 2)
	relative_fps = round(total_fps / benchmark_cycles, 2)
	return\
	[
		facefusion.globals.target_path,
		benchmark_cycles,
		average_run,
		fastest_run,
		slowest_run,
		relative_fps
	]


def clear() -> Update:
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.update(value = None)
