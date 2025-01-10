import os
import subprocess
import tempfile
from typing import List, Optional

from tqdm import tqdm

from facefusion import ffmpeg_builder, logger, process_manager, state_manager, wording
from facefusion.filesystem import get_file_format, remove_file
from facefusion.temp_helper import get_temp_file_path, get_temp_frames_pattern, resolve_temp_frame_paths
from facefusion.typing import AudioBuffer, Commands, Fps, UpdateProgress, VideoPreset
from facefusion.vision import count_trim_frame_total, detect_video_duration, restrict_video_fps


def run_ffmpeg_with_progress(commands : Commands, update_progress : UpdateProgress) -> subprocess.Popen[bytes]:
	log_level = state_manager.get_item('log_level')
	commands.extend(ffmpeg_builder.stream_progress())
	commands.extend(ffmpeg_builder.set_log_level('error'))
	commands = ffmpeg_builder.run(commands)
	process = subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

	while process_manager.is_processing():
		try:

			while __line__ := process.stdout.readline().decode().lower():
				if 'frame=' in __line__:
					_, frame_number = __line__.split('frame=')
					update_progress(int(frame_number))

			if log_level == 'debug':
				log_debug(process)
			process.wait(timeout = 0.5)
		except subprocess.TimeoutExpired:
			continue
		return process

	if process_manager.is_stopping():
		process.terminate()
	return process


def run_ffmpeg(commands : Commands) -> subprocess.Popen[bytes]:
	log_level = state_manager.get_item('log_level')
	commands.extend(ffmpeg_builder.set_log_level('error'))
	commands = ffmpeg_builder.run(commands)
	process = subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

	while process_manager.is_processing():
		try:
			if log_level == 'debug':
				log_debug(process)
			process.wait(timeout = 0.5)
		except subprocess.TimeoutExpired:
			continue
		return process

	if process_manager.is_stopping():
		process.terminate()
	return process


def open_ffmpeg(commands : Commands) -> subprocess.Popen[bytes]:
	commands.extend(ffmpeg_builder.set_log_level('quiet'))
	commands = ffmpeg_builder.run(commands)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def log_debug(process : subprocess.Popen[bytes]) -> None:
	_, stderr = process.communicate()
	errors = stderr.decode().split(os.linesep)

	for error in errors:
		if error.strip():
			logger.debug(error.strip(), __name__)


def extract_frames(target_path : str, temp_video_resolution : str, temp_video_fps : Fps, trim_frame_start : int, trim_frame_end : int) -> bool:
	extract_frame_total = count_trim_frame_total(target_path, trim_frame_start, trim_frame_end)
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

	with tqdm(total = extract_frame_total, desc = wording.get('extracting'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		process = run_ffmpeg_with_progress(commands, lambda frame_number: progress.update(frame_number - progress.n))
		return process.returncode == 0


def copy_image(target_path : str, temp_image_resolution : str) -> bool:
	temp_file_path = get_temp_file_path(target_path)
	if get_file_format(target_path) == 'webp':
		output_image_compression = 100
	else:
		output_image_compression = 1
	commands = [ '-i', target_path, '-s', str(temp_image_resolution), '-q:v', str(output_image_compression), '-y', temp_file_path ]
	return run_ffmpeg(commands).returncode == 0


def finalize_image(target_path : str, output_path : str, output_image_resolution : str) -> bool:
	output_image_quality = state_manager.get_item('output_image_quality')
	temp_file_path = get_temp_file_path(target_path)
	if get_file_format(target_path) == 'webp':
		output_image_compression = output_image_quality
	else:
		output_image_compression = round(31 - (output_image_quality * 0.31))
	commands = [ '-i', temp_file_path, '-s', str(output_image_resolution), '-q:v', str(output_image_compression), '-y', output_path ]
	return run_ffmpeg(commands).returncode == 0


def read_audio_buffer(target_path : str, sample_rate : int, channel_total : int) -> Optional[AudioBuffer]:
	commands = [ '-i', target_path, '-vn', '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', str(sample_rate), '-ac', str(channel_total), '-' ]
	process = open_ffmpeg(commands)
	audio_buffer, _ = process.communicate()
	if process.returncode == 0:
		return audio_buffer
	return None


def restore_audio(target_path : str, output_path : str, output_video_fps : Fps, trim_frame_start : int, trim_frame_end : int) -> bool:
	output_audio_encoder = state_manager.get_item('output_audio_encoder')
	output_audio_quality = state_manager.get_item('output_audio_quality')
	output_audio_volume = state_manager.get_item('output_audio_volume')
	temp_file_path = get_temp_file_path(target_path)
	temp_video_duration = detect_video_duration(temp_file_path)

	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input_path(temp_file_path),
		ffmpeg_builder.set_media_range(trim_frame_start, trim_frame_end, output_video_fps),
		ffmpeg_builder.set_input_path(target_path),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.set_audio_encoder(output_audio_encoder),
		ffmpeg_builder.set_audio_quality(output_audio_encoder, output_audio_quality),
		ffmpeg_builder.set_audio_volume(output_audio_volume),
		ffmpeg_builder.select_media_stream('0:v:0'),
		ffmpeg_builder.select_media_stream('1:a:0'),
		ffmpeg_builder.set_video_duration(temp_video_duration),
		ffmpeg_builder.force_output_path(output_path)
	)
	return run_ffmpeg(commands).returncode == 0


def replace_audio(target_path : str, audio_path : str, output_path : str) -> bool:
	output_audio_encoder = state_manager.get_item('output_audio_encoder')
	output_audio_quality = state_manager.get_item('output_audio_quality')
	output_audio_volume = state_manager.get_item('output_audio_volume')
	temp_file_path = get_temp_file_path(target_path)
	temp_video_duration = detect_video_duration(temp_file_path)

	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input_path(temp_file_path),
		ffmpeg_builder.set_input_path(audio_path),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.set_audio_encoder(output_audio_encoder),
		ffmpeg_builder.set_audio_quality(output_audio_encoder, output_audio_quality),
		ffmpeg_builder.set_audio_volume(output_audio_volume),
		ffmpeg_builder.set_video_duration(temp_video_duration),
		ffmpeg_builder.force_output_path(output_path)
	)
	return run_ffmpeg(commands).returncode == 0


def merge_video(target_path : str, output_video_resolution : str, output_video_fps: Fps) -> bool:
	output_video_encoder = state_manager.get_item('output_video_encoder')
	output_video_quality = state_manager.get_item('output_video_quality')
	output_video_preset = state_manager.get_item('output_video_preset')
	merge_frame_total = len(resolve_temp_frame_paths(target_path))
	temp_video_fps = restrict_video_fps(target_path, output_video_fps)
	temp_file_path = get_temp_file_path(target_path)
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%08d')

	if get_file_format(target_path) == 'webm':
		output_video_encoder = 'libvpx-vp9'
	commands = [ '-r', str(temp_video_fps), '-i', temp_frames_pattern, '-s', str(output_video_resolution), '-c:v', output_video_encoder ]
	if output_video_encoder in [ 'libx264', 'libx265' ]:
		output_video_compression = round(51 - (output_video_quality * 0.51))
		commands.extend([ '-crf', str(output_video_compression), '-preset', output_video_preset ])
	if output_video_encoder in [ 'libvpx-vp9' ]:
		output_video_compression = round(63 - (output_video_quality * 0.63))
		commands.extend([ '-crf', str(output_video_compression) ])
	if output_video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		output_video_compression = round(51 - (output_video_quality * 0.51))
		commands.extend([ '-cq', str(output_video_compression), '-preset', map_nvenc_preset(output_video_preset) ])
	if output_video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		output_video_compression = round(51 - (output_video_quality * 0.51))
		commands.extend([ '-qp_i', str(output_video_compression), '-qp_p', str(output_video_compression), '-quality', map_amf_preset(output_video_preset) ])
	if output_video_encoder in [ 'h264_videotoolbox', 'hevc_videotoolbox' ]:
		commands.extend([ '-q:v', str(output_video_quality) ])
	commands.extend([ '-vf', 'framerate=fps=' + str(output_video_fps), '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-y', temp_file_path ])

	with tqdm(total = merge_frame_total, desc = wording.get('merging'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		process = run_ffmpeg_with_progress(commands, lambda frame_number: progress.update(frame_number - progress.n))
		return process.returncode == 0


def concat_video(output_path : str, temp_output_paths : List[str]) -> bool:
	concat_video_path = tempfile.mktemp()

	with open(concat_video_path, 'w') as concat_video_file:
		for temp_output_path in temp_output_paths:
			concat_video_file.write('file \'' + os.path.abspath(temp_output_path) + '\'' + os.linesep)
		concat_video_file.flush()
		concat_video_file.close()

	output_path = os.path.abspath(output_path)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.use_concat_demuxer(),
		ffmpeg_builder.set_input_path(concat_video_file.name),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.copy_audio_encoder(),
		ffmpeg_builder.force_output_path(output_path)
	)
	process = run_ffmpeg(commands)
	process.communicate()
	remove_file(concat_video_path)
	return process.returncode == 0


def map_nvenc_preset(output_video_preset : VideoPreset) -> Optional[str]:
	if output_video_preset in [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast' ]:
		return 'fast'
	if output_video_preset == 'medium':
		return 'medium'
	if output_video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'slow'
	return None


def map_amf_preset(output_video_preset : VideoPreset) -> Optional[str]:
	if output_video_preset in [ 'ultrafast', 'superfast', 'veryfast' ]:
		return 'speed'
	if output_video_preset in [ 'faster', 'fast', 'medium' ]:
		return 'balanced'
	if output_video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'quality'
	return None


def map_qsv_preset(output_video_preset : VideoPreset) -> Optional[str]:
	if output_video_preset in [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast' ]:
		return 'fast'
	if output_video_preset == 'medium':
		return 'medium'
	if output_video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'slow'
	return None
