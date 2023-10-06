from typing import Any, Optional, List, Dict, Generator
import time
import tempfile
import statistics
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.face_analyser import get_face_analyser
from facefusion.face_cache import clear_faces_cache
from facefusion.processors.frame.core import get_frame_processors_modules
from facefusion.vision import count_video_frame_total
from facefusion.core import limit_resources, conditional_process
from facefusion.utilities import normalize_output_path, clear_temp
from facefusion.uis.core import get_ui_component

BENCHMARK_RESULTS_DATAFRAME : Optional[gradio.Dataframe] = None
BENCHMARK_START_BUTTON : Optional[gradio.Button] = None
BENCHMARK_CLEAR_BUTTON : Optional[gradio.Button] = None
BENCHMARKS : Dict[str, str] =\
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
	global BENCHMARK_START_BUTTON
	global BENCHMARK_CLEAR_BUTTON

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
	BENCHMARK_START_BUTTON = gradio.Button(
		value = wording.get('start_button_label'),
		variant = 'primary',
		size = 'sm'
	)
	BENCHMARK_CLEAR_BUTTON = gradio.Button(
		value = wording.get('clear_button_label'),
		size = 'sm'
	)


def listen() -> None:
	benchmark_runs_checkbox_group = get_ui_component('benchmark_runs_checkbox_group')
	benchmark_cycles_slider = get_ui_component('benchmark_cycles_slider')
	if benchmark_runs_checkbox_group and benchmark_cycles_slider:
		BENCHMARK_START_BUTTON.click(start, inputs = [ benchmark_runs_checkbox_group, benchmark_cycles_slider ], outputs = BENCHMARK_RESULTS_DATAFRAME)
	BENCHMARK_CLEAR_BUTTON.click(clear, outputs = BENCHMARK_RESULTS_DATAFRAME)


def start(benchmark_runs : List[str], benchmark_cycles : int) -> Generator[List[Any], None, None]:
	facefusion.globals.source_path = '.assets/examples/source.jpg'
	target_paths = [ BENCHMARKS[benchmark_run] for benchmark_run in benchmark_runs if benchmark_run in BENCHMARKS ]
	benchmark_results = []
	if target_paths:
		pre_process()
		for target_path in target_paths:
			benchmark_results.append(benchmark(target_path, benchmark_cycles))
			yield benchmark_results
		post_process()


def pre_process() -> None:
	limit_resources()
	get_face_analyser()
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		frame_processor_module.get_frame_processor()


def post_process() -> None:
	clear_faces_cache()


def benchmark(target_path : str, benchmark_cycles : int) -> List[Any]:
	process_times = []
	total_fps = 0.0
	for i in range(benchmark_cycles):
		facefusion.globals.target_path = target_path
		facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, tempfile.gettempdir())
		video_frame_total = count_video_frame_total(facefusion.globals.target_path)
		start_time = time.perf_counter()
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


def clear() -> gradio.Dataframe:
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.Dataframe(value = None)
