import itertools
import shutil

from facefusion.filesystem import get_file_format
from facefusion.typing import AudioEncoder, Commands, Duration, Fps


def run(commands : Commands) -> Commands:
	return [ shutil.which('ffmpeg') ] + commands


def chain(*commands : Commands) -> Commands:
	return list(itertools.chain(*commands))


def set_log_level(log_level : str) -> Commands:
	return [ '-loglevel', log_level ]


def set_progress() -> Commands:
	return [ '-progress' ]


def set_input(input_path : str) -> Commands:
	return [ '-i', input_path ]


def set_output(output_path : str) -> Commands:
	return [ output_path ]


def force_output(output_path : str) -> Commands:
	return [ '-y', output_path ]


def stream_output() -> Commands:
	return [ '-' ]


def unsafe_concat() -> Commands:
	return [ '-f', 'concat', '-safe', '0' ]


def select_frame_range(frame_start : int, frame_end : int, video_fps : Fps) -> Commands:
	if isinstance(frame_start, int) and isinstance(frame_end, int):
		return [ '-vf', 'trim=start_frame=' + str(frame_start) + ':end_frame=' + str(frame_end) + ',fps=' + str(video_fps) ]
	if isinstance(frame_start, int):
		return ['-vf', 'trim=start_frame=' + str(frame_start) + ',fps=' + str(video_fps) ]
	if isinstance(frame_end, int):
		return [ '-vf', 'trim=end_frame=' + str(frame_end) + ',fps=' + str(video_fps) ]
	return [ '-vf', 'fps=' + str(video_fps) ]


def prevent_frame_drop() -> Commands:
	return [ '-vsync', '0' ]


def select_media_range(frame_start : int, frame_end : int, media_fps : Fps) -> Commands:
	commands = []

	if isinstance(frame_start, int):
		commands.extend([ '-ss', str(frame_start / media_fps) ])
	if isinstance(frame_end, int):
		commands.extend([ '-to', str(frame_end / media_fps) ])
	return commands


def select_media_stream(media_stream : str) -> Commands:
	return [ '-map', media_stream ]


def set_media_resolution(video_resolution : str) -> Commands:
	return [ '-s', video_resolution ]


def set_image_quality(image_path : str, image_quality : int) -> Commands:
	if get_file_format(image_path) == 'webp':
		image_compression = image_quality
	else:
		image_compression = round(31 - (image_quality * 0.31))
	return [ '-q:v', str(image_compression) ]


def set_audio_encoder(audio_codec : str) -> Commands:
	return [ '-c:a', audio_codec ]


def copy_audio_encoder() -> Commands:
	return set_audio_encoder('copy')


def set_audio_quality(audio_encoder : AudioEncoder, audio_quality : int) -> Commands:
	if audio_encoder in [ 'aac' ]:
		audio_compression = round(10 - (audio_quality * 0.9))
		return ['-q:a', str(audio_compression)]
	if audio_encoder in [ 'libmp3lame' ]:
		audio_compression = round(9 - (audio_quality * 0.9))
		return ['-q:a', str(audio_compression)]
	if audio_encoder in [ 'libopus', 'libvorbis' ]:
		audio_compression = round((100 - audio_quality) / 10)
		return [ '-q:a', str(audio_compression) ]
	return []


def set_audio_volume(audio_volume : int) -> Commands:
	return [ '-filter:a', 'volume=' + str(audio_volume / 100) ]


def set_video_codec(video_codec : str) -> Commands:
	return [ '-c:v', video_codec ]


def copy_video_encoder() -> Commands:
	return set_video_codec('copy')


def set_video_quality(video_quality : int) -> Commands:
	return [ '-q:v', str(video_quality) ]


def set_video_duration(video_duration : Duration) -> Commands:
	return [ '-t', str(video_duration) ]
