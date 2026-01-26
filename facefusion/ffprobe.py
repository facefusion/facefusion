import os
import subprocess
from typing import Dict, List, Optional

from facefusion import ffprobe_builder
from facefusion.types import Command


def run_ffprobe(commands : List[Command]) -> subprocess.Popen[bytes]:
	commands = ffprobe_builder.run(commands)
	return subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)


def get_audio_entries(audio_path : str) -> Dict[str, str]:
	audio_entries = {}
	commands = ffprobe_builder.chain(
		ffprobe_builder.show_entries([ 'duration', 'sample_rate', 'channels', 'nb_read_frames' ]),
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


def detect_audio_sample_rate(audio_path : str) -> Optional[int]:
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
