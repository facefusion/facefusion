from typing import Any, Optional, List
import time
import tempfile
import statistics
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.capturer import get_video_frame_total
from facefusion.core import conditional_process
from facefusion.uis.typing import Update
from facefusion.utilities import normalize_output_path, clear_temp

BENCHMARK_RESULT_DATAFRAME : Optional[gradio.Dataframe] = None
BENCHMARK_CYCLES_SLIDER : Optional[gradio.Button] = None
BENCHMARK_START_BUTTON : Optional[gradio.Button] = None
BENCHMARK_CLEAR_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global BENCHMARK_RESULT_DATAFRAME
	global BENCHMARK_CYCLES_SLIDER
	global BENCHMARK_START_BUTTON
	global BENCHMARK_CLEAR_BUTTON

	with gradio.Box():
		BENCHMARK_RESULT_DATAFRAME = gradio.Dataframe(
			label = wording.get('benchmark_result_dataframe_label'),
			headers =
			[
				'target_path',
				'benchmark_cycles',
				'average_run',
				'fastest_run',
				'slowest_run',
				'relative_fps'
			],
			col_count = (6, 'fixed'),
			row_count = (6, 'fixed'),
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
	BENCHMARK_START_BUTTON.click(update, inputs = BENCHMARK_CYCLES_SLIDER, outputs = BENCHMARK_RESULT_DATAFRAME)
	BENCHMARK_CLEAR_BUTTON.click(clear, outputs = BENCHMARK_RESULT_DATAFRAME)


def update(benchmark_cycles : int) -> Update:
	facefusion.globals.source_path = '.assets/examples/source.jpg'
	target_paths =\
	[
		'.assets/examples/target-240p.mp4',
		'.assets/examples/target-360p.mp4',
		'.assets/examples/target-540p.mp4',
		'.assets/examples/target-720p.mp4',
		'.assets/examples/target-1080p.mp4',
		'.assets/examples/target-1440p.mp4',
		'.assets/examples/target-2160p.mp4'
	]
	value = [ benchmark(target_path, benchmark_cycles) for target_path in target_paths ]
	return gradio.update(value = value)


def benchmark(target_path : str, benchmark_cycles : int) -> List[Any]:
	process_times = []
	total_fps = 0.0
	for i in range(benchmark_cycles + 1):
		facefusion.globals.target_path = target_path
		facefusion.globals.output_path = normalize_output_path(facefusion.globals.source_path, facefusion.globals.target_path, tempfile.gettempdir())
		video_frame_total = get_video_frame_total(facefusion.globals.target_path)
		start_time = time.perf_counter()
		conditional_process()
		end_time = time.perf_counter()
		process_time = end_time - start_time
		fps = video_frame_total / process_time
		if i > 0:
			process_times.append(process_time)
			total_fps += fps
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
