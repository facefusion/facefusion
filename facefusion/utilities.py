import glob
import mimetypes
import os
import platform
import shutil
import ssl
import subprocess
import tempfile
import urllib
from pathlib import Path
from typing import List, Optional

import onnxruntime
from tqdm import tqdm

import facefusion.globals
from facefusion import wording

TEMP_DIRECTORY_PATH = os.path.join(tempfile.gettempdir(), 'facefusion')
TEMP_OUTPUT_NAME = 'temp.mp4'

# monkey patch ssl
if platform.system().lower() == 'darwin':
	ssl._create_default_https_context = ssl._create_unverified_context


def run_ffmpeg(args : List[str]) -> bool:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	try:
		subprocess.check_output(commands, stderr = subprocess.STDOUT)
		return True
	except subprocess.CalledProcessError:
		return False


def detect_fps(target_path : str) -> Optional[float]:
	commands = [ 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers = 1:nokey = 1', target_path ]
	output = subprocess.check_output(commands).decode().strip().split('/')
	try:
		numerator, denominator = map(int, output)
		return numerator / denominator
	except (ValueError, ZeroDivisionError):
		return None


def extract_frames(target_path : str, fps : float) -> bool:
	temp_directory_path = get_temp_directory_path(target_path)
	temp_frame_quality = round(31 - (facefusion.globals.temp_frame_quality * 0.31))
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	commands = [ '-hwaccel', 'auto', '-i', target_path, '-q:v', str(temp_frame_quality), '-pix_fmt', 'rgb24', ]
	if trim_frame_start is not None and trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ':end_frame=' + str(trim_frame_end) + ',fps=' + str(fps) ])
	elif trim_frame_start is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ',fps=' + str(fps) ])
	elif trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=end_frame=' + str(trim_frame_end) + ',fps=' + str(fps) ])
	else:
		commands.extend([ '-vf', 'fps=' + str(fps) ])
	commands.extend([os.path.join(temp_directory_path, '%04d.' + facefusion.globals.temp_frame_format)])
	return run_ffmpeg(commands)


def create_video(target_path : str, fps : float) -> bool:
	temp_output_path = get_temp_output_path(target_path)
	temp_directory_path = get_temp_directory_path(target_path)
	output_video_quality = round(51 - (facefusion.globals.output_video_quality * 0.5))
	commands = [ '-hwaccel', 'auto', '-r', str(fps), '-i', os.path.join(temp_directory_path, '%04d.' + facefusion.globals.temp_frame_format), '-c:v', facefusion.globals.output_video_encoder ]
	if facefusion.globals.output_video_encoder in [ 'libx264', 'libx265', 'libvpx' ]:
		commands.extend([ '-crf', str(output_video_quality) ])
	if facefusion.globals.output_video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		commands.extend([ '-cq', str(output_video_quality) ])
	commands.extend([ '-pix_fmt', 'yuv420p', '-vf', 'colorspace=bt709:iall=bt601-6-625', '-y', temp_output_path ])
	return run_ffmpeg(commands)


def restore_audio(target_path : str, output_path : str) -> None:
	fps = detect_fps(target_path)
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	temp_output_path = get_temp_output_path(target_path)
	commands = [ '-hwaccel', 'auto', '-i', temp_output_path, '-i', target_path ]
	if trim_frame_start is None and trim_frame_end is None:
		commands.extend([ '-c:a', 'copy' ])
	else:
		if trim_frame_start is not None:
			start_time = trim_frame_start / fps
			commands.extend([ '-ss', str(start_time) ])
		else:
			commands.extend([ '-ss', '0' ])
		if trim_frame_end is not None:
			end_time = trim_frame_end / fps
			commands.extend([ '-to', str(end_time) ])
		commands.extend([ '-c:a', 'aac' ])
	commands.extend([ '-map', '0:v:0', '-map', '1:a:0', '-y', output_path ])
	done = run_ffmpeg(commands)
	if not done:
		move_temp(target_path, output_path)


def get_temp_frame_paths(target_path : str) -> List[str]:
	temp_directory_path = get_temp_directory_path(target_path)
	return glob.glob((os.path.join(glob.escape(temp_directory_path), '*.' + facefusion.globals.temp_frame_format)))


def get_temp_directory_path(target_path : str) -> str:
	target_name, _ = os.path.splitext(os.path.basename(target_path))
	return os.path.join(TEMP_DIRECTORY_PATH, target_name)


def get_temp_output_path(target_path : str) -> str:
	temp_directory_path = get_temp_directory_path(target_path)
	return os.path.join(temp_directory_path, TEMP_OUTPUT_NAME)


def normalize_output_path(source_path : str, target_path : str, output_path : str) -> Optional[str]:
	if source_path and target_path and output_path:
		source_name, _ = os.path.splitext(os.path.basename(source_path))
		target_name, target_extension = os.path.splitext(os.path.basename(target_path))
		if os.path.isdir(output_path):
			return os.path.join(output_path, source_name + '-' + target_name + target_extension)
	return output_path


def create_temp(target_path : str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	Path(temp_directory_path).mkdir(parents = True, exist_ok = True)


def move_temp(target_path : str, output_path : str) -> None:
	temp_output_path = get_temp_output_path(target_path)
	if os.path.isfile(temp_output_path):
		if os.path.isfile(output_path):
			os.remove(output_path)
		shutil.move(temp_output_path, output_path)


def clear_temp(target_path : str) -> None:
	temp_directory_path = get_temp_directory_path(target_path)
	parent_directory_path = os.path.dirname(temp_directory_path)
	if not facefusion.globals.keep_temp and os.path.isdir(temp_directory_path):
		shutil.rmtree(temp_directory_path)
	if os.path.exists(parent_directory_path) and not os.listdir(parent_directory_path):
		os.rmdir(parent_directory_path)


def is_image(image_path : str) -> bool:
	if image_path and os.path.isfile(image_path):
		mimetype, _ = mimetypes.guess_type(image_path)
		return bool(mimetype and mimetype.startswith('image/'))
	return False


def is_video(video_path : str) -> bool:
	if video_path and os.path.isfile(video_path):
		mimetype, _ = mimetypes.guess_type(video_path)
		return bool(mimetype and mimetype.startswith('video/'))
	return False


def conditional_download(download_directory_path : str, urls : List[str]) -> None:
	if not os.path.exists(download_directory_path):
		os.makedirs(download_directory_path)
	for url in urls:
		download_file_path = os.path.join(download_directory_path, os.path.basename(url))
		if not os.path.exists(download_file_path):
			request = urllib.request.urlopen(url) # type: ignore[attr-defined]
			total = int(request.headers.get('Content-Length', 0))
			with tqdm(total = total, desc = wording.get('downloading'), unit = 'B', unit_scale = True, unit_divisor = 1024) as progress:
				urllib.request.urlretrieve(url, download_file_path, reporthook = lambda count, block_size, total_size: progress.update(block_size)) # type: ignore[attr-defined]


def resolve_relative_path(path : str) -> str:
	return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def list_module_names(path : str) -> Optional[List[str]]:
	if os.path.exists(path):
		files = os.listdir(path)
		return [Path(file).stem for file in files if not Path(file).stem.startswith('__')]
	return None


def encode_execution_providers(execution_providers : List[str]) -> List[str]:
	return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers : List[str]) -> List[str]:
	return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers())) if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]
