from typing import Optional, List, Tuple
from functools import lru_cache
import cv2
import numpy
from cv2.typing import Size

from facefusion.common_helper import is_windows
from facefusion.typing import VisionFrame, Resolution, Fps
from facefusion.choices import image_template_sizes, video_template_sizes
from facefusion.filesystem import is_image, is_video, sanitize_path_for_windows


@lru_cache(maxsize = 128)
def read_static_image(image_path : str) -> Optional[VisionFrame]:
	return read_image(image_path)


def read_static_images(image_paths : List[str]) -> Optional[List[VisionFrame]]:
	frames = []
	if image_paths:
		for image_path in image_paths:
			frames.append(read_static_image(image_path))
	return frames


def read_image(image_path : str) -> Optional[VisionFrame]:
	if is_image(image_path):
		if is_windows():
			image_path = sanitize_path_for_windows(image_path)
		return cv2.imread(image_path)
	return None


def write_image(image_path : str, vision_frame : VisionFrame) -> bool:
	if image_path:
		if is_windows():
			image_path = sanitize_path_for_windows(image_path)
		return cv2.imwrite(image_path, vision_frame)
	return False


def detect_image_resolution(image_path : str) -> Optional[Resolution]:
	if is_image(image_path):
		image = read_image(image_path)
		height, width = image.shape[:2]
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
		for template_size in image_template_sizes:
			temp_resolutions.append(normalize_resolution((width * template_size, height * template_size)))
		temp_resolutions = sorted(set(temp_resolutions))
		for temp_resolution in temp_resolutions:
			resolutions.append(pack_resolution(temp_resolution))
	return resolutions


def get_video_frame(video_path : str, frame_number : int = 0) -> Optional[VisionFrame]:
	if is_video(video_path):
		if is_windows():
			video_path = sanitize_path_for_windows(video_path)
		video_capture = cv2.VideoCapture(video_path)
		if video_capture.isOpened():
			frame_total = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
			video_capture.set(cv2.CAP_PROP_POS_FRAMES, min(frame_total, frame_number - 1))
			has_vision_frame, vision_frame = video_capture.read()
			video_capture.release()
			if has_vision_frame:
				return vision_frame
	return None


def count_video_frame_total(video_path : str) -> int:
	if is_video(video_path):
		if is_windows():
			video_path = sanitize_path_for_windows(video_path)
		video_capture = cv2.VideoCapture(video_path)
		if video_capture.isOpened():
			video_frame_total = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
			video_capture.release()
			return video_frame_total
	return 0


def detect_video_fps(video_path : str) -> Optional[float]:
	if is_video(video_path):
		if is_windows():
			video_path = sanitize_path_for_windows(video_path)
		video_capture = cv2.VideoCapture(video_path)
		if video_capture.isOpened():
			video_fps = video_capture.get(cv2.CAP_PROP_FPS)
			video_capture.release()
			return video_fps
	return None


def restrict_video_fps(video_path : str, fps : Fps) -> Fps:
	if is_video(video_path):
		video_fps = detect_video_fps(video_path)
		if video_fps < fps:
			return video_fps
	return fps


def detect_video_resolution(video_path : str) -> Optional[Resolution]:
	if is_video(video_path):
		if is_windows():
			video_path = sanitize_path_for_windows(video_path)
		video_capture = cv2.VideoCapture(video_path)
		if video_capture.isOpened():
			width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
			height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
			video_capture.release()
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
		for template_size in video_template_sizes:
			if width > height:
				temp_resolutions.append(normalize_resolution((template_size * width / height, template_size)))
			else:
				temp_resolutions.append(normalize_resolution((template_size, template_size * height / width)))
		temp_resolutions = sorted(set(temp_resolutions))
		for temp_resolution in temp_resolutions:
			resolutions.append(pack_resolution(temp_resolution))
	return resolutions


def normalize_resolution(resolution : Tuple[float, float]) -> Resolution:
	width, height = resolution

	if width and height:
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


def resize_frame_resolution(vision_frame : VisionFrame, max_resolution : Resolution) -> VisionFrame:
	height, width = vision_frame.shape[:2]
	max_width, max_height = max_resolution

	if height > max_height or width > max_width:
		scale = min(max_height / height, max_width / width)
		new_width = int(width * scale)
		new_height = int(height * scale)
		return cv2.resize(vision_frame, (new_width, new_height))
	return vision_frame


def normalize_frame_color(vision_frame : VisionFrame) -> VisionFrame:
	return cv2.cvtColor(vision_frame, cv2.COLOR_BGR2RGB)


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
