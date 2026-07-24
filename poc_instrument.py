import numpy

from facefusion import process_manager, state_manager, video_manager
from facefusion.types import VideoReader, VisionFrameSet

FRAME_STORE_SET = {}
COUNTER = { 'decode': 0, 'refresh': 0 }

BUFFER_MARGIN = 16
FRAME_OFFSET = 2

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


def run_current(video_path : str, frame_total : int) -> None:
	video_manager.clear_video_pool()
	video_reader = video_manager.get_reader(video_path)

	for frame_number in range(frame_total):
		video_manager.read_video_reader_window(video_reader, max(frame_number - FRAME_OFFSET, 0), frame_number + FRAME_OFFSET)


def run_store(video_path : str, frame_total : int) -> None:
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


def main() -> None:
	state_manager.init_item('temp_pixel_format', 'bgr24')
	process_manager.start()
	video_path = '.assets/examples/target-240p.mp4'
	frame_total = 250

	COUNTER['decode'] = 0
	COUNTER['refresh'] = 0
	run_current(video_path, frame_total)
	print('current -> decodes:', COUNTER.get('decode'), 'refreshes:', COUNTER.get('refresh'))

	COUNTER['decode'] = 0
	COUNTER['refresh'] = 0
	run_store(video_path, frame_total)
	print('store   -> decodes:', COUNTER.get('decode'), 'refreshes:', COUNTER.get('refresh'))


main()
