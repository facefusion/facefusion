import os
import subprocess
from typing import List, Optional

from facefusion import ffprobe_builder
from facefusion.types import Command


def run_ffprobe(commands : List[Command]) -> subprocess.Popen[bytes]:
	commands = ffprobe_builder.run(commands)
	return subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)


def detect_audio_sample_rate(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_audio_stream(0),
		ffprobe_builder.show_stream_entries([ 'sample_rate' ]),
		ffprobe_builder.format_to_value(),
		ffprobe_builder.set_input(audio_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if process.returncode == 0 and output:
		return int(output.decode().strip())
	return None


def detect_audio_channel_total(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_audio_stream(0),
		ffprobe_builder.show_stream_entries([ 'channels' ]),
		ffprobe_builder.format_to_value(),
		ffprobe_builder.set_input(audio_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if process.returncode == 0 and output:
		return int(output.decode().strip())
	return None


def detect_audio_frame_total(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_audio_stream(0),
		ffprobe_builder.show_stream_entries([ 'duration', 'sample_rate' ]),
		ffprobe_builder.format_to_key_value(),
		ffprobe_builder.set_input(audio_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if process.returncode == 0 and output:
		duration = None
		sample_rate = None
		lines = output.decode().strip().split(os.linesep)

		for line in lines:
			if line.startswith('duration='):
				duration = float(line.split('=')[1])
			if line.startswith('sample_rate='):
				sample_rate = int(line.split('=')[1])

		if duration and sample_rate:
			return int(duration * sample_rate)

	return None


def detect_audio_format(audio_path : str) -> Optional[str]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.select_audio_stream(0),
		ffprobe_builder.show_stream_entries([ 'codec_name' ]),
		ffprobe_builder.format_to_value(),
		ffprobe_builder.set_input(audio_path)
	)
	process = run_ffprobe(commands)
	output, _ = process.communicate()

	if process.returncode == 0 and output:
		return output.decode().strip()
	return None
