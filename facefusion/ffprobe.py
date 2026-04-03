import os
import subprocess
from typing import Dict, List, Optional

from facefusion import ffprobe_builder
from facefusion.types import BitRate, Command, Duration, Fps, Resolution, SampleRate


def run_ffprobe(commands : List[Command]) -> subprocess.Popen[bytes]:
	commands = ffprobe_builder.run(commands)
	return subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)


def get_audio_entries(audio_path : str) -> Dict[str, str]:
	audio_entries = {}
	commands = ffprobe_builder.chain(
		ffprobe_builder.show_entries([ 'codec_name', 'duration', 'sample_rate', 'channels', 'nb_read_frames', 'bit_rate' ]),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(audio_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if output:
		lines = output.decode().strip().split(os.linesep)

		for line in lines:
			if '=' in line:
				key, value = line.split('=', 1)
				audio_entries[key] = value

	return audio_entries


def detect_audio_codec(audio_path : str) -> Optional[str]:
	audio_entries = get_audio_entries(audio_path)
	return audio_entries.get('codec_name')


def detect_audio_sample_rate(audio_path : str) -> Optional[SampleRate]:
	audio_entries = get_audio_entries(audio_path)
	sample_rate = audio_entries.get('sample_rate')

	if sample_rate:
		return int(sample_rate)
	return None


def detect_audio_channel_total(audio_path : str) -> Optional[int]:
	audio_entries = get_audio_entries(audio_path)
	audio_channel_total = audio_entries.get('channels')

	if audio_channel_total:
		return int(audio_channel_total)
	return None


def detect_audio_frame_total(audio_path : str) -> Optional[int]:
	audio_entries = get_audio_entries(audio_path)
	audio_duration = audio_entries.get('duration')
	audio_sample_rate = audio_entries.get('sample_rate')

	if audio_duration and audio_sample_rate:
		return int(float(audio_duration) * int(audio_sample_rate))
	return None


def detect_audio_bitrate(audio_path : str) -> Optional[BitRate]:
	audio_entries = get_audio_entries(audio_path)
	bitrate = audio_entries.get('bit_rate')

	if bitrate:
		return int(bitrate)
	return None


def get_video_entries(video_path : str) -> Dict[str, str]:
	video_entries = {}
	commands = ffprobe_builder.chain(
		ffprobe_builder.show_entries([ 'codec_name', 'duration', 'width', 'height', 'r_frame_rate', 'bit_rate' ]),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(video_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if output:
		lines = output.decode().strip().split(os.linesep)

		for line in lines:
			if '=' in line:
				key, value = line.split('=', 1)
				video_entries[key] = value

	return video_entries


def detect_video_codec(video_path : str) -> Optional[str]:
	video_entries = get_video_entries(video_path)
	return video_entries.get('codec_name')


def detect_video_fps(video_path : str) -> Optional[Fps]:
	video_entries = get_video_entries(video_path)
	frame_rate = video_entries.get('r_frame_rate')

	if frame_rate and '/' in frame_rate:
		numerator, denominator = frame_rate.split('/')
		if int(denominator):
			return int(numerator) / int(denominator)
	return None


def detect_video_duration(video_path : str) -> Optional[Duration]:
	video_entries = get_video_entries(video_path)
	duration = video_entries.get('duration')

	if duration:
		return round(float(duration))
	return None


def detect_video_resolution(video_path : str) -> Optional[Resolution]:
	video_entries = get_video_entries(video_path)
	width = video_entries.get('width')
	height = video_entries.get('height')

	if width and height:
		return int(width), int(height)
	return None


def detect_video_bitrate(video_path : str) -> Optional[BitRate]:
	video_entries = get_video_entries(video_path)
	bitrate = video_entries.get('bit_rate')

	if bitrate:
		return int(bitrate)
	return None
