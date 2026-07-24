import numpy

from facefusion import process_manager, state_manager, video_manager

FRAME_STORE_SET = {}
BUFFER_MARGIN = 16
FRAME_OFFSET = 2


def frame_set_bytes(frame_set) -> int:
	return sum(vision_frame.nbytes for vision_frame in frame_set.values())


def run_current(video_path, frame_total):
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)
	peak_count = 0
	peak_bytes = 0

	for frame_number in range(frame_total):
		frame_set = video_manager.read_video_reader_window(video_reader, max(frame_number - FRAME_OFFSET, 0), frame_number + FRAME_OFFSET)
		peak_count = max(peak_count, len(frame_set))
		peak_bytes = max(peak_bytes, frame_set_bytes(frame_set))

	return peak_count, peak_bytes


def run_store(video_path, frame_total):
	video_manager.clear_video_pool()
	FRAME_STORE_SET.clear()
	video_reader = video_manager.get_reader(video_path)
	peak_count = 0
	peak_bytes = 0

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

		peak_count = max(peak_count, len(frame_store))
		peak_bytes = max(peak_bytes, frame_set_bytes(frame_store))

	return peak_count, peak_bytes


def main():
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()

	for video_path in [ '.assets/examples/target-240p.mp4', '.assets/examples/target-1080p.mp4' ]:
		current_count, current_bytes = run_current(video_path, 250)
		store_count, store_bytes = run_store(video_path, 250)
		print(video_path)
		print('  current peak frames:', current_count, 'peak MB:', round(current_bytes / 1024 ** 2, 1))
		print('  store   peak frames:', store_count, 'peak MB:', round(store_bytes / 1024 ** 2, 1))


main()
