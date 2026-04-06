import subprocess
from typing import Dict, List

from facefusion import ffprobe_builder
from facefusion.types import AudioMetadata, Command, Fps, VideoMetadata


def run_ffprobe(commands : List[Command]) -> subprocess.Popen[bytes]:
	commands = ffprobe_builder.run(commands)
	return subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)


def probe_entries(media_path : str, entries : List[str]) -> Dict[str, str]:
	media_entries = {}

	commands = ffprobe_builder.chain(
		ffprobe_builder.show_entries(entries),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(media_path)
	)
	output, _ = run_ffprobe(commands).communicate()

	if output:
		lines = output.decode().strip().splitlines()

		for line in lines:
			if '=' in line:
				key, value = line.split('=', 1)
				media_entries[key] = value

	return media_entries


def extract_audio_metadata(audio_path : str) -> AudioMetadata:
	audio_entries = probe_entries(audio_path, [ 'duration', 'sample_rate', 'channels', 'bit_rate' ])

	duration = float(audio_entries.get('duration'))
	sample_rate = int(audio_entries.get('sample_rate'))
	frame_total = int(duration * sample_rate)
	channel_total = int(audio_entries.get('channels'))
	bit_rate = int(audio_entries.get('bit_rate'))

	audio_metadata : AudioMetadata =\
	{
		'duration' : duration,
		'frame_total' : frame_total,
		'channel_total' : channel_total,
		'sample_rate' : sample_rate,
		'bit_rate' : bit_rate
	}

	return audio_metadata


def extract_video_metadata(video_path : str) -> VideoMetadata:
	video_entries = probe_entries(video_path, [ 'duration', 'width', 'height', 'r_frame_rate', 'bit_rate' ])

	duration = float(video_entries.get('duration'))
	fps = extract_video_fps(video_entries.get('r_frame_rate'))
	frame_total = int(duration * fps)
	width = int(video_entries.get('width'))
	height = int(video_entries.get('height'))
	bit_rate = int(video_entries.get('bit_rate'))

	video_metadata : VideoMetadata =\
	{
		'duration' : duration,
		'frame_total' : frame_total,
		'fps' : fps,
		'resolution' : (width, height),
		'bit_rate' : bit_rate
	}

	return video_metadata


def extract_video_fps(frame_rate : str) -> Fps:
	if frame_rate and '/' in frame_rate:
		numerator, denominator = frame_rate.split('/')

		if int(numerator) and int(denominator):
			return int(numerator) / int(denominator)

	return 0.0
