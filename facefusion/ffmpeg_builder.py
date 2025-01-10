import itertools
import shutil

from facefusion.typing import AudioEncoder, Commands, Duration, Fps


def run(commands : Commands) -> Commands:
	return [ shutil.which('ffmpeg') ] + commands


def chain(*commands : Commands) -> Commands:
	return list(itertools.chain(*commands))


def set_log_level(log_level : str) -> Commands:
	return [ '-loglevel', log_level ]


def stream_progress() -> Commands:
	return [ '-progress', '-' ]


def set_input_path(input_path : str) -> Commands:
	return [ '-i', input_path ]


def set_output_path(output_path : str) -> Commands:
	return [ output_path ]


def force_output_path(output_path : str) -> Commands:
	return [ '-y', output_path ]


def use_concat_demuxer() -> Commands:
	return [ '-f', 'concat', '-safe', '0' ]


def select_media_stream(media_stream : str) -> Commands:
	return [ '-map', media_stream ]


def set_media_range(frame_start : int, frame_end : int, media_fps : Fps) -> Commands:
	commands = []

	if frame_start:
		commands.extend([ '-ss', str(frame_start / media_fps) ])
	if frame_end:
		commands.extend([ '-to', str(frame_end / media_fps) ])
	return commands


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


def set_video_duration(video_duration : Duration) -> Commands:
	return [ '-t', str(video_duration) ]
