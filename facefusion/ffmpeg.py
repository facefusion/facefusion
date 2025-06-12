import os
import subprocess
import tempfile
from functools import partial
from typing import List, Optional, cast

from tqdm import tqdm

import facefusion.choices
from facefusion import ffmpeg_builder, logger, process_manager, state_manager, wording
from facefusion.filesystem import get_file_format, remove_file
from facefusion.temp_helper import get_temp_file_path, get_temp_frames_pattern
from facefusion.types import AudioBuffer, AudioEncoder, Commands, EncoderSet, Fps, UpdateProgress, VideoEncoder, VideoFormat
from facefusion.vision import detect_video_duration, detect_video_fps, predict_video_frame_total


def run_ffmpeg_with_progress(commands : Commands, update_progress : UpdateProgress) -> subprocess.Popen[bytes]:
	log_level = state_manager.get_item('log_level')
	commands.extend(ffmpeg_builder.set_progress())
	commands.extend(ffmpeg_builder.cast_stream())
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


def update_progress(progress : tqdm, frame_number : int) -> None:
	progress.update(frame_number - progress.n)


def run_ffmpeg(commands : Commands) -> subprocess.Popen[bytes]:
	log_level = state_manager.get_item('log_level')
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
	commands = ffmpeg_builder.run(commands)
	return subprocess.Popen(commands, stdin = subprocess.PIPE, stdout = subprocess.PIPE)


def log_debug(process : subprocess.Popen[bytes]) -> None:
	_, stderr = process.communicate()
	errors = stderr.decode().split(os.linesep)

	for error in errors:
		if error.strip():
			logger.debug(error.strip(), __name__)


def get_available_encoder_set() -> EncoderSet:
	available_encoder_set : EncoderSet =\
	{
		'audio': [],
		'video': []
	}
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.get_encoders()
	)
	process = run_ffmpeg(commands)

	while line := process.stdout.readline().decode().lower():
		if line.startswith(' a'):
			audio_encoder = line.split()[1]

			if audio_encoder in facefusion.choices.output_audio_encoders:
				index = facefusion.choices.output_audio_encoders.index(audio_encoder) #type:ignore[arg-type]
				available_encoder_set['audio'].insert(index, audio_encoder) #type:ignore[arg-type]
		if line.startswith(' v'):
			video_encoder = line.split()[1]

			if video_encoder in facefusion.choices.output_video_encoders:
				index = facefusion.choices.output_video_encoders.index(video_encoder) #type:ignore[arg-type]
				available_encoder_set['video'].insert(index, video_encoder) #type:ignore[arg-type]

	return available_encoder_set


def extract_frames(target_path : str, temp_video_resolution : str, temp_video_fps : Fps, trim_frame_start : int, trim_frame_end : int) -> bool:
	extract_frame_total = predict_video_frame_total(target_path, temp_video_fps, trim_frame_start, trim_frame_end)
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%08d')
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(target_path),
		ffmpeg_builder.set_media_resolution(temp_video_resolution),
		ffmpeg_builder.set_frame_quality(0),
		ffmpeg_builder.select_frame_range(trim_frame_start, trim_frame_end, temp_video_fps),
		ffmpeg_builder.prevent_frame_drop(),
		ffmpeg_builder.set_output(temp_frames_pattern)
	)

	with tqdm(total = extract_frame_total, desc = wording.get('extracting'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		process = run_ffmpeg_with_progress(commands, partial(update_progress, progress))
		return process.returncode == 0


def copy_image(target_path : str, temp_image_resolution : str) -> bool:
	temp_image_path = get_temp_file_path(target_path)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(target_path),
		ffmpeg_builder.set_media_resolution(temp_image_resolution),
		ffmpeg_builder.set_image_quality(target_path, 100),
		ffmpeg_builder.force_output(temp_image_path)
	)
	return run_ffmpeg(commands).returncode == 0


def finalize_image(target_path : str, output_path : str, output_image_resolution : str) -> bool:
	output_image_quality = state_manager.get_item('output_image_quality')
	temp_image_path = get_temp_file_path(target_path)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(temp_image_path),
		ffmpeg_builder.set_media_resolution(output_image_resolution),
		ffmpeg_builder.set_image_quality(target_path, output_image_quality),
		ffmpeg_builder.force_output(output_path)
	)
	return run_ffmpeg(commands).returncode == 0


def read_audio_buffer(target_path : str, audio_sample_rate : int, audio_sample_size : int, audio_channel_total : int) -> Optional[AudioBuffer]:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(target_path),
		ffmpeg_builder.ignore_video_stream(),
		ffmpeg_builder.set_audio_sample_rate(audio_sample_rate),
		ffmpeg_builder.set_audio_sample_size(audio_sample_size),
		ffmpeg_builder.set_audio_channel_total(audio_channel_total),
		ffmpeg_builder.cast_stream()
	)

	process = open_ffmpeg(commands)
	audio_buffer, _ = process.communicate()
	if process.returncode == 0:
		return audio_buffer
	return None


def restore_audio(target_path : str, output_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
	output_audio_encoder = state_manager.get_item('output_audio_encoder')
	output_audio_quality = state_manager.get_item('output_audio_quality')
	output_audio_volume = state_manager.get_item('output_audio_volume')
	target_video_fps = detect_video_fps(target_path)
	temp_video_path = get_temp_file_path(target_path)
	temp_video_format = cast(VideoFormat, get_file_format(temp_video_path))
	temp_video_duration = detect_video_duration(temp_video_path)

	output_audio_encoder = fix_audio_encoder(temp_video_format, output_audio_encoder)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(temp_video_path),
		ffmpeg_builder.select_media_range(trim_frame_start, trim_frame_end, target_video_fps),
		ffmpeg_builder.set_input(target_path),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.set_audio_encoder(output_audio_encoder),
		ffmpeg_builder.set_audio_quality(output_audio_encoder, output_audio_quality),
		ffmpeg_builder.set_audio_volume(output_audio_volume),
		ffmpeg_builder.select_media_stream('0:v:0'),
		ffmpeg_builder.select_media_stream('1:a:0'),
		ffmpeg_builder.set_video_duration(temp_video_duration),
		ffmpeg_builder.force_output(output_path)
	)
	return run_ffmpeg(commands).returncode == 0


def replace_audio(target_path : str, audio_path : str, output_path : str) -> bool:
	output_audio_encoder = state_manager.get_item('output_audio_encoder')
	output_audio_quality = state_manager.get_item('output_audio_quality')
	output_audio_volume = state_manager.get_item('output_audio_volume')
	temp_video_path = get_temp_file_path(target_path)
	temp_video_format = cast(VideoFormat, get_file_format(temp_video_path))
	temp_video_duration = detect_video_duration(temp_video_path)

	output_audio_encoder = fix_audio_encoder(temp_video_format, output_audio_encoder)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input(temp_video_path),
		ffmpeg_builder.set_input(audio_path),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.set_audio_encoder(output_audio_encoder),
		ffmpeg_builder.set_audio_quality(output_audio_encoder, output_audio_quality),
		ffmpeg_builder.set_audio_volume(output_audio_volume),
		ffmpeg_builder.set_video_duration(temp_video_duration),
		ffmpeg_builder.force_output(output_path)
	)
	return run_ffmpeg(commands).returncode == 0


def merge_video(target_path : str, temp_video_fps : Fps, output_video_resolution : str, output_video_fps : Fps, trim_frame_start : int, trim_frame_end : int) -> bool:
	output_video_encoder = state_manager.get_item('output_video_encoder')
	output_video_quality = state_manager.get_item('output_video_quality')
	output_video_preset = state_manager.get_item('output_video_preset')
	merge_frame_total = predict_video_frame_total(target_path, output_video_fps, trim_frame_start, trim_frame_end)
	temp_video_path = get_temp_file_path(target_path)
	temp_video_format = cast(VideoFormat, get_file_format(temp_video_path))
	temp_frames_pattern = get_temp_frames_pattern(target_path, '%08d')

	output_video_encoder = fix_video_encoder(temp_video_format, output_video_encoder)
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_input_fps(temp_video_fps),
		ffmpeg_builder.set_input(temp_frames_pattern),
		ffmpeg_builder.set_media_resolution(output_video_resolution),
		ffmpeg_builder.set_video_encoder(output_video_encoder),
		ffmpeg_builder.set_video_quality(output_video_encoder, output_video_quality),
		ffmpeg_builder.set_video_preset(output_video_encoder, output_video_preset),
		ffmpeg_builder.set_video_fps(output_video_fps),
		ffmpeg_builder.set_pixel_format(output_video_encoder),
		ffmpeg_builder.set_video_colorspace('bt709'),
		ffmpeg_builder.force_output(temp_video_path)
	)

	with tqdm(total = merge_frame_total, desc = wording.get('merging'), unit = 'frame', ascii = ' =', disable = state_manager.get_item('log_level') in [ 'warn', 'error' ]) as progress:
		process = run_ffmpeg_with_progress(commands, partial(update_progress, progress))
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
		ffmpeg_builder.unsafe_concat(),
		ffmpeg_builder.set_input(concat_video_file.name),
		ffmpeg_builder.copy_video_encoder(),
		ffmpeg_builder.copy_audio_encoder(),
		ffmpeg_builder.force_output(output_path)
	)
	process = run_ffmpeg(commands)
	process.communicate()
	remove_file(concat_video_path)
	return process.returncode == 0


def fix_audio_encoder(video_format : VideoFormat, audio_encoder : AudioEncoder) -> AudioEncoder:
	if video_format == 'avi' and audio_encoder == 'libopus':
		return 'aac'
	if video_format == 'm4v':
		return 'aac'
	if video_format == 'mov' and audio_encoder in [ 'flac', 'libopus' ]:
		return 'aac'
	if video_format == 'webm':
		return 'libopus'
	return audio_encoder


def fix_video_encoder(video_format : VideoFormat, video_encoder : VideoEncoder) -> VideoEncoder:
	if video_format == 'm4v':
		return 'libx264'
	if video_format in [ 'mkv', 'mp4' ] and video_encoder == 'rawvideo':
		return 'libx264'
	if video_format == 'mov' and video_encoder == 'libvpx-vp9':
		return 'libx264'
	if video_format == 'webm':
		return 'libvpx-vp9'
	return video_encoder
