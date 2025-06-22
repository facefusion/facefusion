import hashlib
import os
import statistics
import tempfile
from time import perf_counter
from typing import Generator, List

import facefusion.choices
from facefusion import core, state_manager
from facefusion.cli_helper import render_table
from facefusion.download import conditional_download, resolve_download_url
from facefusion.filesystem import get_file_extension
from facefusion.types import BenchmarkCycleSet
from facefusion.vision import count_video_frame_total, detect_video_fps, detect_video_resolution, pack_resolution


def pre_check() -> bool:
	conditional_download('.assets/examples',
	[
		resolve_download_url('examples-3.0.0', 'source.jpg'),
		resolve_download_url('examples-3.0.0', 'source.mp3'),
		resolve_download_url('examples-3.0.0', 'target-240p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-360p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-540p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-720p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-1080p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-1440p.mp4'),
		resolve_download_url('examples-3.0.0', 'target-2160p.mp4')
	])
	return True


def run() -> Generator[List[BenchmarkCycleSet], None, None]:
	benchmark_resolutions = state_manager.get_item('benchmark_resolutions')
	benchmark_cycle_count = state_manager.get_item('benchmark_cycle_count')

	state_manager.init_item('source_paths', [ '.assets/examples/source.jpg', '.assets/examples/source.mp3' ])
	state_manager.init_item('face_landmarker_score', 0)
	state_manager.init_item('temp_frame_format', 'bmp')
	state_manager.init_item('output_audio_volume', 0)
	state_manager.init_item('output_video_preset', 'ultrafast')
	state_manager.init_item('video_memory_strategy', 'tolerant')

	benchmarks = []
	target_paths = [facefusion.choices.benchmark_set.get(benchmark_resolution) for benchmark_resolution in benchmark_resolutions if benchmark_resolution in facefusion.choices.benchmark_set]

	for target_path in target_paths:
		state_manager.set_item('target_path', target_path)
		state_manager.set_item('output_path', suggest_output_path(state_manager.get_item('target_path')))
		benchmarks.append(cycle(benchmark_cycle_count))
		yield benchmarks


def cycle(cycle_count : int) -> BenchmarkCycleSet:
	process_times = []
	video_frame_total = count_video_frame_total(state_manager.get_item('target_path'))
	output_video_resolution = detect_video_resolution(state_manager.get_item('target_path'))
	state_manager.set_item('output_video_resolution', pack_resolution(output_video_resolution))
	state_manager.set_item('output_video_fps', detect_video_fps(state_manager.get_item('target_path')))

	core.conditional_process()

	for index in range(cycle_count):
		start_time = perf_counter()
		core.conditional_process()
		end_time = perf_counter()
		process_times.append(end_time - start_time)

	average_run = round(statistics.mean(process_times), 2)
	fastest_run = round(min(process_times), 2)
	slowest_run = round(max(process_times), 2)
	relative_fps = round(video_frame_total * cycle_count / sum(process_times), 2)

	return\
	{
		'target_path': state_manager.get_item('target_path'),
		'cycle_count': cycle_count,
		'average_run': average_run,
		'fastest_run': fastest_run,
		'slowest_run': slowest_run,
		'relative_fps': relative_fps
	}


def suggest_output_path(target_path : str) -> str:
	target_file_extension = get_file_extension(target_path)
	return os.path.join(tempfile.gettempdir(), hashlib.sha1().hexdigest()[:8] + target_file_extension)


def render() -> None:
	benchmarks = []
	headers =\
	[
		'target_path',
		'cycle_count',
		'average_run',
		'fastest_run',
		'slowest_run',
		'relative_fps'
	]

	for benchmark in run():
		benchmarks = benchmark

	contents = [ list(benchmark_set.values()) for benchmark_set in benchmarks ]
	render_table(headers, contents)
