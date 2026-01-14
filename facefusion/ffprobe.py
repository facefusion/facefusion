import subprocess
from typing import List, Optional

from facefusion import ffprobe_builder
from facefusion.types import Command


def run_ffprobe(commands : List[Command]) -> Optional[str]:
	commands = ffprobe_builder.run(commands)
	process = subprocess.Popen(commands, stderr = subprocess.PIPE, stdout = subprocess.PIPE)

	try:
		output, _ = process.communicate()
		if process.returncode == 0 and output:
			return output.decode().strip()
	except (OSError, UnicodeDecodeError):
		pass
	return None


def detect_audio_sample_rate(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(),
		ffprobe_builder.show_entries('stream=sample_rate'),
		ffprobe_builder.set_output_value_only(),
		ffprobe_builder.set_input(audio_path)
	)
	output = run_ffprobe(commands)

	if output:
		return int(output)
	return None


def detect_audio_channel_total(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(),
		ffprobe_builder.show_entries('stream=channels'),
		ffprobe_builder.set_output_value_only(),
		ffprobe_builder.set_input(audio_path)
	)
	output = run_ffprobe(commands)

	if output:
		return int(output)
	return None


def detect_audio_frame_total(audio_path : str) -> Optional[int]:
	commands = ffprobe_builder.chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(),
		ffprobe_builder.show_entries('stream=nb_frames'),
		ffprobe_builder.set_output_value_only(),
		ffprobe_builder.set_input(audio_path)
	)
	output = run_ffprobe(commands)

	if output and output != 'N/A':
		return int(output)

	commands = ffprobe_builder.chain(
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(),
		ffprobe_builder.show_entries('stream=duration,sample_rate'),
		ffprobe_builder.set_output_key_value(),
		ffprobe_builder.set_input(audio_path)
	)
	output = run_ffprobe(commands)

	if output:
		duration = None
		sample_rate = None
		lines = output.split('\n')

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
		ffprobe_builder.set_error_level(),
		ffprobe_builder.select_audio_stream(),
		ffprobe_builder.show_entries('stream=codec_name'),
		ffprobe_builder.set_output_value_only(),
		ffprobe_builder.set_input(audio_path)
	)
	return run_ffprobe(commands)
