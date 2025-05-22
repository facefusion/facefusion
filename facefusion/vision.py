import math
from functools import lru_cache
from typing import List, Optional, Tuple

import cv2
import numpy
from cv2.typing import Size

import facefusion.choices
from facefusion.common_helper import is_windows
from facefusion.filesystem import get_file_extension, is_image, is_video
from facefusion.thread_helper import thread_semaphore
from facefusion.types import Duration, Fps, Orientation, Resolution, VisionFrame
from facefusion.video_manager import get_video_capture


@lru_cache()
def read_static_image(image_path : str) -> Optional[VisionFrame]:
	return read_image(image_path)


def read_static_images(image_paths : List[str]) -> List[VisionFrame]:
	frames = []

	if image_paths:
		for image_path in image_paths:
			frames.append(read_static_image(image_path))
	return frames


def read_image(image_path : str) -> Optional[VisionFrame]:
	if is_image(image_path):
		if is_windows():
			image_buffer = numpy.fromfile(image_path, dtype = numpy.uint8)
			return cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)
		return cv2.imread(image_path)
	return None


def write_image(image_path : str, vision_frame : VisionFrame) -> bool:
	if image_path:
		if is_windows():
			image_file_extension = get_file_extension(image_path)
			_, vision_frame = cv2.imencode(image_file_extension, vision_frame)
			vision_frame.tofile(image_path)
			return is_image(image_path)
		return cv2.imwrite(image_path, vision_frame)
	return False


def detect_image_resolution(image_path : str) -> Optional[Resolution]:
	if is_image(image_path):
		image = read_image(image_path)
		height, width = image.shape[:2]

		if width > 0 and height > 0:
			return width, height
	return None


def restrict_image_resolution(image_path : str, resolution : Resolution) -> Resolution:
	if is_image(image_path):
		image_resolution = detect_image_resolution(image_path)
		if image_resolution < resolution:
			return image_resolution
	return resolution


def create_image_resolutions(resolution : Resolution) -> List[str]:
	resolutions = []
	temp_resolutions = []

	if resolution:
		width, height = resolution
		temp_resolutions.append(normalize_resolution(resolution))
		for image_template_size in facefusion.choices.image_template_sizes:
			temp_resolutions.append(normalize_resolution((width * image_template_size, height * image_template_size)))
		temp_resolutions = sorted(set(temp_resolutions))
		for temp_resolution in temp_resolutions:
			resolutions.append(pack_resolution(temp_resolution))
	return resolutions


def read_video_frame(video_path : str, frame_number : int = 0) -> Optional[VisionFrame]:
	if is_video(video_path):
		video_capture = get_video_capture(video_path)

		if video_capture.isOpened():
			frame_total = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)

			with thread_semaphore():
				video_capture.set(cv2.CAP_PROP_POS_FRAMES, min(frame_total, frame_number - 1))
				has_vision_frame, vision_frame = video_capture.read()

			if has_vision_frame:
				return vision_frame

	return None


def count_video_frame_total(video_path : str) -> int:
	if is_video(video_path):
		video_capture = get_video_capture(video_path)

		if video_capture.isOpened():
			with thread_semaphore():
				video_frame_total = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
				return video_frame_total

	return 0


def predict_video_frame_total(video_path : str, fps : Fps, trim_frame_start : int, trim_frame_end : int) -> int:
	if is_video(video_path):
		video_fps = detect_video_fps(video_path)
		extract_frame_total = count_trim_frame_total(video_path, trim_frame_start, trim_frame_end) * fps / video_fps
		return math.floor(extract_frame_total)
	return 0


def detect_video_fps(video_path : str) -> Optional[float]:
	if is_video(video_path):
		video_capture = get_video_capture(video_path)

		if video_capture.isOpened():
			with thread_semaphore():
				video_fps = video_capture.get(cv2.CAP_PROP_FPS)
				return video_fps

	return None


def restrict_video_fps(video_path : str, fps : Fps) -> Fps:
	if is_video(video_path):
		video_fps = detect_video_fps(video_path)
		if video_fps < fps:
			return video_fps
	return fps


def detect_video_duration(video_path : str) -> Duration:
	video_frame_total = count_video_frame_total(video_path)
	video_fps = detect_video_fps(video_path)

	if video_frame_total and video_fps:
		return video_frame_total / video_fps
	return 0


def count_trim_frame_total(video_path : str, trim_frame_start : Optional[int], trim_frame_end : Optional[int]) -> int:
	trim_frame_start, trim_frame_end = restrict_trim_frame(video_path, trim_frame_start, trim_frame_end)

	return trim_frame_end - trim_frame_start


def restrict_trim_frame(video_path : str, trim_frame_start : Optional[int], trim_frame_end : Optional[int]) -> Tuple[int, int]:
	video_frame_total = count_video_frame_total(video_path)

	if isinstance(trim_frame_start, int):
		trim_frame_start = max(0, min(trim_frame_start, video_frame_total))
	if isinstance(trim_frame_end, int):
		trim_frame_end = max(0, min(trim_frame_end, video_frame_total))

	if isinstance(trim_frame_start, int) and isinstance(trim_frame_end, int):
		return trim_frame_start, trim_frame_end
	if isinstance(trim_frame_start, int):
		return trim_frame_start, video_frame_total
	if isinstance(trim_frame_end, int):
		return 0, trim_frame_end

	return 0, video_frame_total


def detect_video_resolution(video_path : str) -> Optional[Resolution]:
	if is_video(video_path):
		video_capture = get_video_capture(video_path)

		if video_capture.isOpened():
			with thread_semaphore():
				width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
				height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
				return int(width), int(height)

	return None


def restrict_video_resolution(video_path : str, resolution : Resolution) -> Resolution:
	if is_video(video_path):
		video_resolution = detect_video_resolution(video_path)
		if video_resolution < resolution:
			return video_resolution
	return resolution


def create_video_resolutions(resolution : Resolution) -> List[str]:
	resolutions = []
	temp_resolutions = []

	if resolution:
		width, height = resolution
		temp_resolutions.append(normalize_resolution(resolution))
		for video_template_size in facefusion.choices.video_template_sizes:
			if width > height:
				temp_resolutions.append(normalize_resolution((video_template_size * width / height, video_template_size)))
			else:
				temp_resolutions.append(normalize_resolution((video_template_size, video_template_size * height / width)))
		temp_resolutions = sorted(set(temp_resolutions))
		for temp_resolution in temp_resolutions:
			resolutions.append(pack_resolution(temp_resolution))
	return resolutions


def normalize_resolution(resolution : Tuple[float, float]) -> Resolution:
	width, height = resolution

	if width > 0 and height > 0:
		normalize_width = round(width / 2) * 2
		normalize_height = round(height / 2) * 2
		return normalize_width, normalize_height
	return 0, 0


def pack_resolution(resolution : Resolution) -> str:
	width, height = normalize_resolution(resolution)
	return str(width) + 'x' + str(height)


def unpack_resolution(resolution : str) -> Resolution:
	width, height = map(int, resolution.split('x'))
	return width, height


def detect_frame_orientation(vision_frame : VisionFrame) -> Orientation:
	height, width = vision_frame.shape[:2]

	if width > height:
		return 'landscape'
	return 'portrait'


def restrict_frame(vision_frame : VisionFrame, resolution : Resolution) -> VisionFrame:
	height, width = vision_frame.shape[:2]
	restrict_width, restrict_height = resolution

	if height > restrict_height or width > restrict_width:
		scale = min(restrict_height / height, restrict_width / width)
		new_width = int(width * scale)
		new_height = int(height * scale)
		return cv2.resize(vision_frame, (new_width, new_height))
	return vision_frame


def fit_frame(vision_frame : VisionFrame, resolution: Resolution) -> VisionFrame:
	fit_width, fit_height = resolution
	height, width = vision_frame.shape[:2]
	scale = min(fit_height / height, fit_width / width)
	new_width = int(width * scale)
	new_height = int(height * scale)
	paste_vision_frame = cv2.resize(vision_frame, (new_width, new_height))
	x_pad = (fit_width - new_width) // 2
	y_pad = (fit_height - new_height) // 2
	temp_vision_frame = numpy.pad(paste_vision_frame, ((y_pad, fit_height - new_height - y_pad), (x_pad, fit_width - new_width - x_pad), (0, 0)))
	return temp_vision_frame


def normalize_frame_color(vision_frame : VisionFrame) -> VisionFrame:
	return cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB)


def conditional_match_frame_color(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame) -> VisionFrame:
	histogram_factor = calc_histogram_difference(source_vision_frame, target_vision_frame)
	target_vision_frame = blend_vision_frames(target_vision_frame, match_frame_color(source_vision_frame, target_vision_frame), histogram_factor)
	return target_vision_frame


def match_frame_color(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame) -> VisionFrame:
	color_difference_sizes = numpy.linspace(16, target_vision_frame.shape[0], 3, endpoint = False)

	for color_difference_size in color_difference_sizes:
		source_vision_frame = equalize_frame_color(source_vision_frame, target_vision_frame, normalize_resolution((color_difference_size, color_difference_size)))
	target_vision_frame = equalize_frame_color(source_vision_frame, target_vision_frame, target_vision_frame.shape[:2][::-1])
	return target_vision_frame


def equalize_frame_color(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame, size : Size) -> VisionFrame:
	source_frame_resize = cv2.resize(source_vision_frame, size, interpolation = cv2.INTER_AREA).astype(numpy.float32)
	target_frame_resize = cv2.resize(target_vision_frame, size, interpolation = cv2.INTER_AREA).astype(numpy.float32)
	color_difference_vision_frame = numpy.subtract(source_frame_resize, target_frame_resize)
	color_difference_vision_frame = cv2.resize(color_difference_vision_frame, target_vision_frame.shape[:2][::-1], interpolation = cv2.INTER_CUBIC)
	target_vision_frame = numpy.add(target_vision_frame, color_difference_vision_frame).clip(0, 255).astype(numpy.uint8)
	return target_vision_frame


def calc_histogram_difference(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame) -> float:
	histogram_source = cv2.calcHist([cv2.cvtColor(source_vision_frame, cv2.COLOR_BGR2HSV)], [ 0, 1 ], None, [ 50, 60 ], [ 0, 180, 0, 256 ])
	histogram_target = cv2.calcHist([cv2.cvtColor(target_vision_frame, cv2.COLOR_BGR2HSV)], [ 0, 1 ], None, [ 50, 60 ], [ 0, 180, 0, 256 ])
	histogram_difference = float(numpy.interp(cv2.compareHist(histogram_source, histogram_target, cv2.HISTCMP_CORREL), [ -1, 1 ], [ 0, 1 ]))
	return histogram_difference


def blend_vision_frames(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame, blend_factor : float) -> VisionFrame:
	blend_vision_frame = cv2.addWeighted(source_vision_frame, 1 - blend_factor, target_vision_frame, blend_factor, 0)
	return blend_vision_frame


def create_tile_frames(vision_frame : VisionFrame, size : Size) -> Tuple[List[VisionFrame], int, int]:
	vision_frame = numpy.pad(vision_frame, ((size[1], size[1]), (size[1], size[1]), (0, 0)))
	tile_width = size[0] - 2 * size[2]
	pad_size_bottom = size[2] + tile_width - vision_frame.shape[0] % tile_width
	pad_size_right = size[2] + tile_width - vision_frame.shape[1] % tile_width
	pad_vision_frame = numpy.pad(vision_frame, ((size[2], pad_size_bottom), (size[2], pad_size_right), (0, 0)))
	pad_height, pad_width = pad_vision_frame.shape[:2]
	row_range = range(size[2], pad_height - size[2], tile_width)
	col_range = range(size[2], pad_width - size[2], tile_width)
	tile_vision_frames = []

	for row_vision_frame in row_range:
		top = row_vision_frame - size[2]
		bottom = row_vision_frame + size[2] + tile_width

		for column_vision_frame in col_range:
			left = column_vision_frame - size[2]
			right = column_vision_frame + size[2] + tile_width
			tile_vision_frames.append(pad_vision_frame[top:bottom, left:right, :])

	return tile_vision_frames, pad_width, pad_height


def merge_tile_frames(tile_vision_frames : List[VisionFrame], temp_width : int, temp_height : int, pad_width : int, pad_height : int, size : Size) -> VisionFrame:
	merge_vision_frame = numpy.zeros((pad_height, pad_width, 3)).astype(numpy.uint8)
	tile_width = tile_vision_frames[0].shape[1] - 2 * size[2]
	tiles_per_row = min(pad_width // tile_width, len(tile_vision_frames))

	for index, tile_vision_frame in enumerate(tile_vision_frames):
		tile_vision_frame = tile_vision_frame[size[2]:-size[2], size[2]:-size[2]]
		row_index = index // tiles_per_row
		col_index = index % tiles_per_row
		top = row_index * tile_vision_frame.shape[0]
		bottom = top + tile_vision_frame.shape[0]
		left = col_index * tile_vision_frame.shape[1]
		right = left + tile_vision_frame.shape[1]
		merge_vision_frame[top:bottom, left:right, :] = tile_vision_frame

	merge_vision_frame = merge_vision_frame[size[1] : size[1] + temp_height, size[1]: size[1] + temp_width, :]
	return merge_vision_frame
