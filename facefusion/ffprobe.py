import subprocess
from functools import lru_cache
from typing import Dict, List

from facefusion import ffprobe_builder
from facefusion.types import AudioMetadata, Buffer, Command, Fps, VideoMetadata


def run_ffprobe(commands : List[Command]) -> subprocess.Popen[Buffer]:
	commands = ffprobe_builder.run(commands)
	return subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)


def parse_entries(output : Buffer) -> Dict[str, str]:
	media_entries = {}

	if output:
		lines = output.decode().strip().splitlines()

		for line in lines:
			if '=' in line:
				key, value = line.split('=', 1)
				media_entries[key] = value

	return media_entries


def probe_audio_entries(audio_path : str, entries : List[str]) -> Dict[str, str]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_stream('a:0'),
		ffprobe_builder.show_stream_entries(entries),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(audio_path)
	)

	output, _ = run_ffprobe(commands).communicate()

	return parse_entries(output)


def probe_video_entries(video_path : str, entries : List[str]) -> Dict[str, str]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_stream('v:0'),
		ffprobe_builder.show_stream_entries(entries),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(video_path)
	)

	output, _ = run_ffprobe(commands).communicate()

	return parse_entries(output)


def probe_format_entries(media_path : str, entries : List[str]) -> Dict[str, str]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.show_format_entries(entries),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(media_path)
	)

	output, _ = run_ffprobe(commands).communicate()

	return parse_entries(output)


@lru_cache(maxsize = 128)
def extract_static_audio_metadata(audio_path : str) -> AudioMetadata:
	return extract_audio_metadata(audio_path)


def extract_audio_metadata(audio_path : str) -> AudioMetadata:
	audio_entries = probe_audio_entries(audio_path, [ 'sample_rate', 'channels' ])
	format_entries = probe_format_entries(audio_path, [ 'duration', 'bit_rate' ])

	duration = float(format_entries.get('duration'))
	sample_rate = int(audio_entries.get('sample_rate'))
	frame_total = round(duration * sample_rate)
	channel_total = int(audio_entries.get('channels'))
	bit_rate = int(format_entries.get('bit_rate'))

	audio_metadata : AudioMetadata =\
	{
		'duration' : duration,
		'frame_total' : frame_total,
		'channel_total' : channel_total,
		'sample_rate' : sample_rate,
		'bit_rate' : bit_rate
	}

	return audio_metadata


@lru_cache(maxsize = 128)
def extract_static_video_metadata(video_path : str) -> VideoMetadata:
	return extract_video_metadata(video_path)


def extract_video_metadata(video_path : str) -> VideoMetadata:
	video_entries = probe_video_entries(video_path, [ 'width', 'height', 'r_frame_rate', 'color_transfer' ])
	format_entries = probe_format_entries(video_path, [ 'duration', 'bit_rate' ])

	duration = float(format_entries.get('duration'))
	fps = extract_video_fps(video_entries.get('r_frame_rate'))
	frame_total = round(duration * fps)
	width = int(video_entries.get('width'))
	height = int(video_entries.get('height'))
	bit_rate = int(format_entries.get('bit_rate'))
	color_transfer = video_entries.get('color_transfer', 'unknown')

	video_metadata : VideoMetadata =\
	{
		'duration' : duration,
		'frame_total' : frame_total,
		'fps' : fps,
		'resolution' : (width, height),
		'bit_rate' : bit_rate,
		'color_transfer' : color_transfer
	}

	return video_metadata


def extract_video_fps(frame_rate : str) -> Fps:
	if frame_rate and '/' in frame_rate:
		numerator, denominator = frame_rate.split('/')

		if int(numerator) and int(denominator):
			return int(numerator) / int(denominator)

	return 0.0
