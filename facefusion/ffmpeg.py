from typing import List, Optional
import os
import subprocess
import filetype

import facefusion.globals
from facefusion import logger, process_manager
from facefusion.typing import OutputVideoPreset, Fps, AudioBuffer
from facefusion.filesystem import get_temp_frames_pattern, get_temp_file_path
from facefusion.vision import restrict_video_fps


def run_ffmpeg(args : List[str]) -> bool:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'error' ]
	commands.extend(args)
	process = subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

	while process_manager.is_processing():
		try:
			if facefusion.globals.log_level == 'debug':
				log_debug(process)
			return process.wait(timeout = 0.5) == 0
		except subprocess.TimeoutExpired:
			continue
	return process.returncode == 0


def open_ffmpeg(args : List[str]) -> subprocess.Popen[bytes]:
	commands = [ 'ffmpeg', '-hide_banner', '-loglevel', 'quiet' ]
	commands.extend(args)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def log_debug(process : subprocess.Popen[bytes]) -> None:
	_, stderr = process.communicate()
	errors = stderr.decode().split(os.linesep)

	for error in errors:
		if error.strip():
			logger.debug(error.strip(), __name__.upper())


def extract_frames(target_path : str, temp_video_resolution : str, temp_video_fps : Fps) -> bool:
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%04d')
	commands = [ '-i', target_path, '-s', str(temp_video_resolution), '-q:v', '0' ]

	if trim_frame_start is not None and trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ':end_frame=' + str(trim_frame_end) + ',fps=' + str(temp_video_fps) ])
	elif trim_frame_start is not None:
		commands.extend([ '-vf', 'trim=start_frame=' + str(trim_frame_start) + ',fps=' + str(temp_video_fps) ])
	elif trim_frame_end is not None:
		commands.extend([ '-vf', 'trim=end_frame=' + str(trim_frame_end) + ',fps=' + str(temp_video_fps) ])
	else:
		commands.extend([ '-vf', 'fps=' + str(temp_video_fps) ])
	commands.extend([ '-vsync', '0', temp_frames_pattern ])
	return run_ffmpeg(commands)


def merge_video(target_path : str, output_video_resolution : str, output_video_fps : Fps) -> bool:
	temp_video_fps = restrict_video_fps(target_path, output_video_fps)
	temp_file_path = get_temp_file_path(target_path)
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%04d')
	commands = [ '-r', str(temp_video_fps), '-i', temp_frames_pattern, '-s', str(output_video_resolution), '-c:v', facefusion.globals.output_video_encoder ]

	if facefusion.globals.output_video_encoder in [ 'libx264', 'libx265' ]:
		output_video_compression = round(51 - (facefusion.globals.output_video_quality * 0.51))
		commands.extend([ '-crf', str(output_video_compression), '-preset', facefusion.globals.output_video_preset ])
	if facefusion.globals.output_video_encoder in [ 'libvpx-vp9' ]:
		output_video_compression = round(63 - (facefusion.globals.output_video_quality * 0.63))
		commands.extend([ '-crf', str(output_video_compression) ])
	if facefusion.globals.output_video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		output_video_compression = round(51 - (facefusion.globals.output_video_quality * 0.51))
		commands.extend([ '-cq', str(output_video_compression), '-preset', map_nvenc_preset(facefusion.globals.output_video_preset) ])
	if facefusion.globals.output_video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		output_video_compression = round(51 - (facefusion.globals.output_video_quality * 0.51))
		commands.extend([ '-qp_i', str(output_video_compression), '-qp_p', str(output_video_compression), '-quality', map_amf_preset(facefusion.globals.output_video_preset) ])
	commands.extend([ '-vf', 'framerate=fps=' + str(output_video_fps), '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-y', temp_file_path ])
	return run_ffmpeg(commands)


def copy_image(target_path : str, temp_image_resolution : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	is_webp = filetype.guess_mime(target_path) == 'image/webp'
	temp_image_compression = 100 if is_webp else 0
	commands = [ '-i', target_path, '-s', str(temp_image_resolution), '-q:v', str(temp_image_compression), '-y', temp_file_path ]
	return run_ffmpeg(commands)


def finalize_image(target_path : str, output_path : str, output_image_resolution : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	output_image_compression = round(31 - (facefusion.globals.output_image_quality * 0.31))
	commands = [ '-i', temp_file_path, '-s', str(output_image_resolution), '-q:v', str(output_image_compression), '-y', output_path ]
	return run_ffmpeg(commands)


def read_audio_buffer(target_path : str, sample_rate : int, channel_total : int) -> Optional[AudioBuffer]:
	commands = [ '-i', target_path, '-vn', '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', str(sample_rate), '-ac', str(channel_total), '-']
	process = open_ffmpeg(commands)
	audio_buffer, _ = process.communicate()
	if process.returncode == 0:
		return audio_buffer
	return None


def restore_audio(target_path : str, output_path : str, output_video_fps : Fps) -> bool:
	trim_frame_start = facefusion.globals.trim_frame_start
	trim_frame_end = facefusion.globals.trim_frame_end
	temp_file_path = get_temp_file_path(target_path)
	commands = [ '-i', temp_file_path ]

	if trim_frame_start is not None:
		start_time = trim_frame_start / output_video_fps
		commands.extend([ '-ss', str(start_time) ])
	if trim_frame_end is not None:
		end_time = trim_frame_end / output_video_fps
		commands.extend([ '-to', str(end_time) ])
	commands.extend([ '-i', target_path, '-c', 'copy', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_path ])
	return run_ffmpeg(commands)


def replace_audio(target_path : str, audio_path : str, output_path : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	commands = [ '-i', temp_file_path, '-i', audio_path, '-af', 'apad', '-shortest', '-y', output_path ]
	return run_ffmpeg(commands)


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
