import statistics
import time

import numpy

from facefusion import process_manager, state_manager, video_manager

FRAME_STORE_SET = {}
BUFFER_MARGIN = 16
FRAME_OFFSET = 2
REPEAT = 8


def run_current(video_path, frame_total):
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)

	for frame_number in range(frame_total):
		video_manager.read_video_reader_window(video_reader, max(frame_number - FRAME_OFFSET, 0), frame_number + FRAME_OFFSET)


def run_store(video_path, frame_total):
	video_manager.clear_video_pool()
	FRAME_STORE_SET.clear()
	video_reader = video_manager.get_reader(video_path)

	for frame_number in range(frame_total):
		frame_start = max(frame_number - FRAME_OFFSET, 0)
		frame_end = frame_number + FRAME_OFFSET

		if video_path not in FRAME_STORE_SET:
			FRAME_STORE_SET[video_path] = {}
		frame_store = FRAME_STORE_SET.get(video_path)

		if frame_start not in frame_store and (frame_start < video_reader.get('position') or frame_start > video_reader.get('position') + BUFFER_MARGIN):
			video_manager.refresh_video_reader(video_reader, frame_start)

		for window_number in range(video_reader.get('position'), frame_end + 1):
			vision_frame = video_manager.read_video_reader_frame(video_reader)

			if numpy.any(vision_frame):
				frame_store[window_number] = vision_frame

		for window_number in list(frame_store):
			if window_number < frame_start - BUFFER_MARGIN:
				del frame_store[window_number]


def measure(run, video_path, frame_total):
	start_time = time.perf_counter()
	run(video_path, frame_total)
	return time.perf_counter() - start_time


def main():
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()
	video_path = '.assets/examples/target-240p.mp4'
	frame_total = 250

	measure(run_current, video_path, frame_total)
	measure(run_store, video_path, frame_total)

	a1 = []
	a2 = []
	b = []

	for _ in range(REPEAT):
		a1.append(measure(run_current, video_path, frame_total))
		a2.append(measure(run_current, video_path, frame_total))
		b.append(measure(run_store, video_path, frame_total))

	print('current-A median:', round(statistics.median(a1), 4))
	print('current-B median:', round(statistics.median(a2), 4))
	print('store    median:', round(statistics.median(b), 4))
	print('A/A delta:', round((statistics.median(a2) - statistics.median(a1)) / statistics.median(a1) * 100, 1), '%')
	print('A/store delta:', round((statistics.median(b) - statistics.median(a1)) / statistics.median(a1) * 100, 1), '%')
	print('all current runs:', [ round(value, 3) for value in a1 + a2 ])
	print('all store runs:', [ round(value, 3) for value in b ])


main()
