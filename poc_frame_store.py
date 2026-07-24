import statistics
import time
from typing import Dict, List, Tuple

import numpy

from facefusion import process_manager, state_manager, video_manager
from facefusion.types import VideoReader, VisionFrame, VisionFrameSet

FRAME_STORE_SET : Dict[str, VisionFrameSet] = {}

BUFFER_MARGIN = 16
FRAME_OFFSET = 2
REPEAT = 6


def get_frame_store(source : str) -> VisionFrameSet:
	if source not in FRAME_STORE_SET:
		FRAME_STORE_SET[source] = {}

	return FRAME_STORE_SET.get(source)


def clear_frame_store() -> None:
	FRAME_STORE_SET.clear()


def read_window_current(video_reader : VideoReader, frame_start : int, frame_end : int) -> VisionFrameSet:
	return video_manager.read_video_reader_window(video_reader, frame_start, frame_end)


def read_window_store(video_reader : VideoReader, source : str, frame_start : int, frame_end : int) -> VisionFrameSet:
	frame_store = get_frame_store(source)

	if frame_start not in frame_store and (frame_start < video_reader.get('position') or frame_start > video_reader.get('position') + BUFFER_MARGIN):
		video_manager.refresh_video_reader(video_reader, frame_start)

	for frame_number in range(video_reader.get('position'), frame_end + 1):
		vision_frame = video_manager.read_video_reader_frame(video_reader)

		if numpy.any(vision_frame):
			frame_store[frame_number] = vision_frame

	for frame_number in list(frame_store):
		if frame_number < frame_start - BUFFER_MARGIN:
			del frame_store[frame_number]

	return frame_store


def select_window(frame_set : VisionFrameSet, frame_number : int) -> List[VisionFrame]:
	vision_frames = []

	for window_number in range(frame_number - FRAME_OFFSET, frame_number + FRAME_OFFSET + 1):
		if window_number in frame_set:
			vision_frames.append(frame_set.get(window_number))

	return vision_frames


def run_current(video_path : str, frame_total : int) -> List[List[VisionFrame]]:
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)
	collected = []

	for frame_number in range(frame_total):
		frame_set = read_window_current(video_reader, max(frame_number - FRAME_OFFSET, 0), frame_number + FRAME_OFFSET)
		collected.append(select_window(frame_set, frame_number))

	return collected


def run_store(video_path : str, frame_total : int) -> List[List[VisionFrame]]:
	video_manager.clear_video_pool()
	clear_frame_store()
	video_reader = video_manager.get_reader(video_path)
	collected = []

	for frame_number in range(frame_total):
		frame_set = read_window_store(video_reader, video_path, max(frame_number - FRAME_OFFSET, 0), frame_number + FRAME_OFFSET)
		collected.append(select_window(frame_set, frame_number))

	return collected


def measure(run, video_path : str, frame_total : int) -> float:
	start_time = time.perf_counter()
	run(video_path, frame_total)
	return time.perf_counter() - start_time


def verify_equal(video_path : str, frame_total : int) -> bool:
	current_windows = run_current(video_path, frame_total)
	store_windows = run_store(video_path, frame_total)
	equal = True

	for frame_number in range(frame_total):
		current_middle = current_windows[frame_number][len(current_windows[frame_number]) // 2]
		store_middle = store_windows[frame_number][len(store_windows[frame_number]) // 2]

		if not numpy.array_equal(current_middle, store_middle):
			equal = False

	return equal


def benchmark(video_path : str) -> Tuple[float, float, int]:
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)
	frame_total = min(video_reader.get('metadata').get('frame_total'), 250)

	measure(run_current, video_path, frame_total)
	measure(run_store, video_path, frame_total)
	current_runs = []
	store_runs = []

	for repeat_number in range(REPEAT):
		if repeat_number % 2 == 0:
			current_runs.append(measure(run_current, video_path, frame_total))
			store_runs.append(measure(run_store, video_path, frame_total))
		if repeat_number % 2 == 1:
			store_runs.append(measure(run_store, video_path, frame_total))
			current_runs.append(measure(run_current, video_path, frame_total))

	return statistics.median(current_runs), statistics.median(store_runs), frame_total


def main() -> None:
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()

	video_paths =\
	[
		'.assets/examples/target-240p.mp4',
		'.assets/examples/target-720p.mp4',
		'.assets/examples/target-1080p.mp4'
	]

	print('video'.ljust(38), 'frames'.rjust(7), 'current(s)'.rjust(12), 'store(s)'.rjust(12), 'delta'.rjust(9), 'equal'.rjust(7))

	for video_path in video_paths:
		current_median, store_median, frame_total = benchmark(video_path)
		equal = verify_equal(video_path, frame_total)
		delta = (store_median - current_median) / current_median * 100
		print(video_path.ljust(38), str(frame_total).rjust(7), f'{current_median:.4f}'.rjust(12), f'{store_median:.4f}'.rjust(12), f'{delta:+.1f}%'.rjust(9), str(equal).rjust(7))

	video_manager.clear_video_pool()
	clear_frame_store()


main()
