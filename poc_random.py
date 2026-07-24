import random
import time

import numpy

from facefusion import frame_store, process_manager, state_manager, video_manager
from facefusion.types import VideoReader

COUNTER = { 'decode': 0, 'refresh': 0 }
BUFFER_MARGIN = 16

real_read_frame = video_manager.read_video_reader_frame
real_refresh = video_manager.refresh_video_reader


def counting_read_frame(video_reader : VideoReader):
	COUNTER['decode'] = COUNTER.get('decode') + 1
	return real_read_frame(video_reader)


def counting_refresh(video_reader : VideoReader, frame_position : int) -> None:
	COUNTER['refresh'] = COUNTER.get('refresh') + 1
	real_refresh(video_reader, frame_position)


video_manager.read_video_reader_frame = counting_read_frame
video_manager.refresh_video_reader = counting_refresh


def baseline_read(video_reader : VideoReader, frame_cache, frame_number : int):
	if frame_number not in frame_cache and (frame_number < video_reader.get('position') or frame_number > video_reader.get('position') + BUFFER_MARGIN):
		video_manager.refresh_video_reader(video_reader, frame_number)
		frame_cache.clear()

	for window_number in range(video_reader.get('position'), frame_number + 1):
		vision_frame = video_manager.read_video_reader_frame(video_reader)

		if numpy.any(vision_frame):
			frame_cache[window_number] = vision_frame

	for window_number in list(frame_cache):
		if window_number < frame_number - BUFFER_MARGIN:
			del frame_cache[window_number]

	return frame_cache.get(frame_number)


def store_read(video_reader : VideoReader, frame_number : int):
	return video_manager.read_video_reader_window(video_reader, frame_number, frame_number).get(frame_number)


def cache_mb(frame_cache) -> float:
	return sum(vision_frame.nbytes for vision_frame in frame_cache.values()) / 1024 ** 2


def run(video_path : str, frame_numbers, mode : str):
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)
	frame_cache = {}
	peak_mb = 0.0
	COUNTER['decode'] = 0
	COUNTER['refresh'] = 0
	start_time = time.perf_counter()

	for frame_number in frame_numbers:
		if mode == 'baseline':
			baseline_read(video_reader, frame_cache, frame_number)
			peak_mb = max(peak_mb, cache_mb(frame_cache))
		if mode == 'store':
			store_read(video_reader, frame_number)
			peak_mb = max(peak_mb, cache_mb(frame_store.get_frame_store(video_path)))

	return COUNTER.get('decode'), COUNTER.get('refresh'), round(time.perf_counter() - start_time, 3), round(peak_mb, 1)


def report(title : str, video_path : str, frame_numbers) -> None:
	base = run(video_path, frame_numbers, 'baseline')
	store = run(video_path, frame_numbers, 'store')
	print(title)
	print('  baseline -> decodes:', base[0], 'refreshes:', base[1], 'time:', base[2], 'peak MB:', base[3])
	print('  store    -> decodes:', store[0], 'refreshes:', store[1], 'time:', store[2], 'peak MB:', store[3])


def main() -> None:
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()
	video_path = '.assets/examples/target-1080p.mp4'
	frame_total = 250

	random.seed(42)
	sequential = list(range(frame_total))
	random_small = [ random.randint(0, 60) for _ in range(frame_total) ]
	random_wide = [ random.randint(0, frame_total - 1) for _ in range(frame_total) ]

	report('sequential (control)', video_path, sequential)
	report('random within 0-60 (revisits)', video_path, random_small)
	report('random within 0-249 (wide)', video_path, random_wide)


main()
