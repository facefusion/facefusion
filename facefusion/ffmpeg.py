import os
import shutil
import subprocess
import tempfile
from typing import List, Optional

import filetype

from facefusion import logger, process_manager, state_manager
from facefusion.filesystem import remove_file
from facefusion.temp_helper import get_temp_file_path, get_temp_frames_pattern
from facefusion.typing import AudioBuffer, Fps, OutputVideoPreset
from facefusion.vision import restrict_video_fps


def run_ffmpeg(args : List[str]) -> subprocess.Popen[bytes]:
	commands = [ shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	process = subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

	while process_manager.is_processing():
		try:
			if state_manager.get_item('log_level') == 'debug':
				log_debug(process)
			process.wait(timeout = 0.5)
		except subprocess.TimeoutExpired:
			continue
		return process

	if process_manager.is_stopping():
		process.terminate()
	return process


def open_ffmpeg(args : List[str]) -> subprocess.Popen[bytes]:
	commands = [ shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'quiet' ]
	commands.extend(args)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def log_debug(process : subprocess.Popen[bytes]) -> None:
	_, stderr = process.communicate()
	errors = stderr.decode().split(os.linesep)

	for error in errors:
		if error.strip():
			logger.debug(error.strip(), __name__)


def extract_frames(target_path : str, temp_video_resolution : str, temp_video_fps : Fps) -> bool:
	trim_frame_start = state_manager.get_item('trim_frame_start')
	trim_frame_end = state_manager.get_item('trim_frame_end')
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%08d')
	commands = [ '-i', target_path, '-s', str(temp_video_resolution), '-q:v', '0' ]

	if isinstance(trim_frame_start, int) and isinstance(trim_frame_end, int):
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ':end_frame=' + str(trim_frame_end) + ',fps=' + str(temp_video_fps) ])
	elif isinstance(trim_frame_start, int):
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ',fps=' + str(temp_video_fps) ])
	elif isinstance(trim_frame_end, int):
		commands.extend([ '-vf', 'trim=end_frame=' + str(trim_frame_end) + ',fps=' + str(temp_video_fps) ])
	else:
		commands.extend([ '-vf', 'fps=' + str(temp_video_fps) ])
	commands.extend([ '-vsync', '0', temp_frames_pattern ])
	return run_ffmpeg(commands).returncode == 0


def merge_video(target_path : str, output_video_resolution : str, output_video_fps : Fps) -> bool:
	temp_video_fps = restrict_video_fps(target_path, output_video_fps)
	temp_file_path = get_temp_file_path(target_path)
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%08d')
	commands = [ '-r', str(temp_video_fps), '-i', temp_frames_pattern, '-s', str(output_video_resolution), '-c:v', state_manager.get_item('output_video_encoder') ]

	if state_manager.get_item('output_video_encoder') in [ 'libx264', 'libx265' ]:
		output_video_compression = round(51 - (state_manager.get_item('output_video_quality') * 0.51))
		commands.extend([ '-crf', str(output_video_compression), '-preset', state_manager.get_item('output_video_preset') ])
	if state_manager.get_item('output_video_encoder') in [ 'libvpx-vp9' ]:
		output_video_compression = round(63 - (state_manager.get_item('output_video_quality') * 0.63))
		commands.extend([ '-crf', str(output_video_compression) ])
	if state_manager.get_item('output_video_encoder') in [ 'h264_nvenc', 'hevc_nvenc' ]:
		output_video_compression = round(51 - (state_manager.get_item('output_video_quality') * 0.51))
		commands.extend([ '-cq', str(output_video_compression), '-preset', map_nvenc_preset(state_manager.get_item('output_video_preset')) ])
	if state_manager.get_item('output_video_encoder') in [ 'h264_amf', 'hevc_amf' ]:
		output_video_compression = round(51 - (state_manager.get_item('output_video_quality') * 0.51))
		commands.extend([ '-qp_i', str(output_video_compression), '-qp_p', str(output_video_compression), '-quality', map_amf_preset(state_manager.get_item('output_video_preset')) ])
	if state_manager.get_item('output_video_encoder') in [ 'h264_videotoolbox', 'hevc_videotoolbox' ]:
		commands.extend([ '-q:v', str(state_manager.get_item('output_video_quality')) ])
	commands.extend([ '-vf', 'framerate=fps=' + str(output_video_fps), '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-y', temp_file_path ])
	return run_ffmpeg(commands).returncode == 0


def concat_video(output_path : str, temp_output_paths : List[str]) -> bool:
	concat_video_path = tempfile.mktemp()

	with open(concat_video_path, 'w') as concat_video_file:
		for temp_output_path in temp_output_paths:
			concat_video_file.write('file \'' + os.path.abspath(temp_output_path) + '\'' + os.linesep)
		concat_video_file.flush()
		concat_video_file.close()
	commands = [ '-f', 'concat', '-safe', '0', '-i', concat_video_file.name, '-c:v', 'copy', '-c:a', state_manager.get_item('output_audio_encoder'), '-y', os.path.abspath(output_path) ]
	process = run_ffmpeg(commands)
	process.communicate()
	remove_file(concat_video_path)
	return process.returncode == 0


def copy_image(target_path : str, temp_image_resolution : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	temp_image_compression = calc_image_compression(target_path, 100)
	commands = [ '-i', target_path, '-s', str(temp_image_resolution), '-q:v', str(temp_image_compression), '-y', temp_file_path ]
	return run_ffmpeg(commands).returncode == 0


def finalize_image(target_path : str, output_path : str, output_image_resolution : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	output_image_compression = calc_image_compression(target_path, state_manager.get_item('output_image_quality'))
	commands = [ '-i', temp_file_path, '-s', str(output_image_resolution), '-q:v', str(output_image_compression), '-y', output_path ]
	return run_ffmpeg(commands).returncode == 0


def calc_image_compression(image_path : str, image_quality : int) -> int:
	is_webp = filetype.guess_mime(image_path) == 'image/webp'
	if is_webp:
		image_quality = 100 - image_quality
	return round(31 - (image_quality * 0.31))


def read_audio_buffer(target_path : str, sample_rate : int, channel_total : int) -> Optional[AudioBuffer]:
	commands = [ '-i', target_path, '-vn', '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', str(sample_rate), '-ac', str(channel_total), '-' ]
	process = open_ffmpeg(commands)
	audio_buffer, _ = process.communicate()
	if process.returncode == 0:
		return audio_buffer
	return None


def restore_audio(target_path : str, output_path : str, output_video_fps : Fps) -> bool:
	trim_frame_start = state_manager.get_item('trim_frame_start')
	trim_frame_end = state_manager.get_item('trim_frame_end')
	temp_file_path = get_temp_file_path(target_path)
	commands = [ '-i', temp_file_path ]

	if isinstance(trim_frame_start, int):
		start_time = trim_frame_start / output_video_fps
		commands.extend([ '-ss', str(start_time) ])
	if isinstance(trim_frame_end, int):
		end_time = trim_frame_end / output_video_fps
		commands.extend([ '-to', str(end_time) ])
	commands.extend([ '-i', target_path, '-c:v', 'copy', '-c:a', state_manager.get_item('output_audio_encoder'), '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path ])
	return run_ffmpeg(commands).returncode == 0


def replace_audio(target_path : str, audio_path : str, output_path : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	commands = [ '-i', temp_file_path, '-i', audio_path, '-c:a', state_manager.get_item('output_audio_encoder'), '-af', 'apad', '-shortest', '-y', output_path ]
	return run_ffmpeg(commands).returncode == 0


def map_nvenc_preset(output_video_preset : OutputVideoPreset) -> Optional[str]:
	if output_video_preset in [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast' ]:
		return 'fast'
	if output_video_preset == 'medium':
		return 'medium'
	if output_video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'slow'
	return None


def map_amf_preset(output_video_preset : OutputVideoPreset) -> Optional[str]:
	if output_video_preset in [ 'ultrafast', 'superfast', 'veryfast' ]:
		return 'speed'
	if output_video_preset in [ 'faster', 'fast', 'medium' ]:
		return 'balanced'
	if output_video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'quality'
	return None
