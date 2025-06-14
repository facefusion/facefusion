from typing import Any, Generator, List, Optional

import gradio

from facefusion import state_manager, wording
from facefusion.benchmarker import BENCHMARKS, benchmark_target, pre_process, suggest_output_path
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
	benchmark_cycles_slider = get_ui_component('benchmark_cycles_slider')

	if benchmark_resolutions_checkbox_group and benchmark_cycles_slider:
		BENCHMARK_START_BUTTON.click(start, inputs = [ benchmark_resolutions_checkbox_group, benchmark_cycles_slider ], outputs = BENCHMARK_BENCHMARKS_DATAFRAME)


def start(benchmark_resolutions : List[str], benchmark_cycles : int) -> Generator[List[Any], None, None]:
	state_manager.set_item('source_paths', [ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ])
	state_manager.set_item('face_landmarker_score', 0)
	state_manager.set_item('temp_frame_format', 'bmp')
	state_manager.set_item('output_audio_volume', 0)
	state_manager.set_item('output_video_preset', 'ultrafast')
	state_manager.set_item('video_memory_strategy', 'tolerant')
	state_manager.sync_item('execution_providers')
	state_manager.sync_item('execution_thread_count')
	state_manager.sync_item('execution_queue_count')
	state_manager.sync_item('system_memory_limit')
	benchmark_results = []
	target_paths = [ BENCHMARKS[benchmark_resolution] for benchmark_resolution in benchmark_resolutions if benchmark_resolution in BENCHMARKS ]

	if target_paths:
		pre_process()
		for target_path in target_paths:
			state_manager.set_item('target_path', target_path)
			state_manager.set_item('output_path', suggest_output_path(state_manager.get_item('target_path')))
			benchmark_results.append(benchmark_target(benchmark_cycles))
			yield benchmark_results


