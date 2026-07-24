import time

from facefusion import process_manager, state_manager, video_manager
from facefusion.types import VideoReader

FRAME_STORE_SET = {}
COUNTER = { 'decode': 0, 'refresh': 0 }
WORKING_SET = 60
PASSES = 3

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


def read_frame_current(video_reader : VideoReader, frame_number : int):
	frame_set = video_manager.read_video_reader_window(video_reader, frame_number, frame_number)
	return frame_set.get(frame_number)


def read_frame_store(video_reader : VideoReader, source : str, frame_number : int):
	if source not in FRAME_STORE_SET:
		FRAME_STORE_SET[source] = {}
	frame_store = FRAME_STORE_SET.get(source)

	if frame_number in frame_store:
		return frame_store.get(frame_number)

	video_manager.conditional_set_video_reader_position(video_reader, frame_number)
	vision_frame = video_manager.read_video_reader_frame(video_reader)
	frame_store[frame_number] = vision_frame
	return vision_frame


def run_current(video_path : str):
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)

	for _ in range(PASSES):
		for frame_number in range(WORKING_SET):
			read_frame_current(video_reader, frame_number)


def run_store(video_path : str):
	video_manager.clear_video_pool()
	FRAME_STORE_SET.clear()
	video_reader = video_manager.get_reader(video_path)

	for _ in range(PASSES):
		for frame_number in range(WORKING_SET):
			read_frame_store(video_reader, video_path, frame_number)


def peak_store_mb() -> float:
	frame_store = FRAME_STORE_SET.get('.assets/examples/target-1080p.mp4')
	return sum(vision_frame.nbytes for vision_frame in frame_store.values()) / 1024 ** 2


def main() -> None:
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()
	video_path = '.assets/examples/target-1080p.mp4'

	COUNTER['decode'] = 0
	COUNTER['refresh'] = 0
	start_time = time.perf_counter()
	run_current(video_path)
	current_time = time.perf_counter() - start_time
	print('current -> decodes:', COUNTER.get('decode'), 'refreshes:', COUNTER.get('refresh'), 'time:', round(current_time, 3))

	COUNTER['decode'] = 0
	COUNTER['refresh'] = 0
	start_time = time.perf_counter()
	run_store(video_path)
	store_time = time.perf_counter() - start_time
	print('store   -> decodes:', COUNTER.get('decode'), 'refreshes:', COUNTER.get('refresh'), 'time:', round(store_time, 3), 'peak MB:', round(peak_store_mb(), 1))


main()
