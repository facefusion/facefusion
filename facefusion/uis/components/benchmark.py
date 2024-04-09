from typing import Any, Optional, List, Dict, Generator
from time import sleep, perf_counter
import tempfile
import statistics
import gradio

import facefusion.globals
from facefusion import process_manager, wording
from facefusion.face_store import clear_static_faces
from facefusion.processors.frame.core import get_frame_processors_modules
from facefusion.vision import count_video_frame_total, detect_video_resolution, detect_video_fps, pack_resolution
from facefusion.core import conditional_process
from facefusion.memory import limit_system_memory
from facefusion.filesystem import clear_temp
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
		label = wording.get('uis.benchmark_results_dataframe'),
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
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	BENCHMARK_CLEAR_BUTTON = gradio.Button(
		value = wording.get('uis.clear_button'),
		size = 'sm'
	)


def listen() -> None:
	benchmark_runs_checkbox_group = get_ui_component('benchmark_runs_checkbox_group')
	benchmark_cycles_slider = get_ui_component('benchmark_cycles_slider')

	if benchmark_runs_checkbox_group and benchmark_cycles_slider:
		BENCHMARK_START_BUTTON.click(start, inputs = [ benchmark_runs_checkbox_group, benchmark_cycles_slider ], outputs = BENCHMARK_RESULTS_DATAFRAME)
	BENCHMARK_CLEAR_BUTTON.click(clear, outputs = BENCHMARK_RESULTS_DATAFRAME)


def start(benchmark_runs : List[str], benchmark_cycles : int) -> Generator[List[Any], None, None]:
	facefusion.globals.source_paths = [ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ]
	facefusion.globals.output_path = tempfile.gettempdir()
	facefusion.globals.face_landmarker_score = 0
	facefusion.globals.temp_frame_format = 'bmp'
	facefusion.globals.output_video_preset = 'ultrafast'
	benchmark_results = []
	target_paths = [ BENCHMARKS[benchmark_run] for benchmark_run in benchmark_runs if benchmark_run in BENCHMARKS ]

	if target_paths:
		pre_process()
		for target_path in target_paths:
			facefusion.globals.target_path = target_path
			benchmark_results.append(benchmark(benchmark_cycles))
			yield benchmark_results
		post_process()


def pre_process() -> None:
	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	for frame_processor_module in get_frame_processors_modules(facefusion.globals.frame_processors):
		frame_processor_module.get_frame_processor()


def post_process() -> None:
	clear_static_faces()


def benchmark(benchmark_cycles : int) -> List[Any]:
	process_times = []
	video_frame_total = count_video_frame_total(facefusion.globals.target_path)
	output_video_resolution = detect_video_resolution(facefusion.globals.target_path)
	facefusion.globals.output_video_resolution = pack_resolution(output_video_resolution)
	facefusion.globals.output_video_fps = detect_video_fps(facefusion.globals.target_path)

	for index in range(benchmark_cycles):
		start_time = perf_counter()
		conditional_process()
		end_time = perf_counter()
		process_times.append(end_time - start_time)
	average_run = round(statistics.mean(process_times), 2)
	fastest_run = round(min(process_times), 2)
	slowest_run = round(max(process_times), 2)
	relative_fps = round(video_frame_total * benchmark_cycles / sum(process_times), 2)

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
	while process_manager.is_processing():
		sleep(0.5)
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.Dataframe(value = None)
