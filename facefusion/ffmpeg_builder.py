import itertools
import shutil
from typing import Optional

from facefusion.filesystem import get_file_format
from facefusion.typing import AudioEncoder, Commands, Duration, Fps, VideoEncoder, VideoPreset


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


def set_input_fps(input_fps : Fps) -> Commands:
	return [ '-r', str(input_fps) ]


def set_output(output_path : str) -> Commands:
	return [ output_path ]


def force_output(output_path : str) -> Commands:
	return [ '-y', output_path ]


def capture_stream() -> Commands:
	return [ '-' ]


def unsafe_concat() -> Commands:
	return [ '-f', 'concat', '-safe', '0' ]


def set_pixel_format(pixel_format : str) -> Commands:
	return [ '-pix_fmt', pixel_format ]


def set_frame_quality(frame_quality : int) -> Commands:
	return [ '-q:v', str(frame_quality) ]


def select_frame_range(frame_start : int, frame_end : int, video_fps : Fps) -> Commands:
	if isinstance(frame_start, int) and isinstance(frame_end, int):
		return [ '-vf', 'trim=start_frame=' + str(frame_start) + ':end_frame=' + str(frame_end) + ',fps=' + str(video_fps) ]
	if isinstance(frame_start, int):
		return [ '-vf', 'trim=start_frame=' + str(frame_start) + ',fps=' + str(video_fps) ]
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


def set_audio_sample_rate(audio_sample_rate : int) -> Commands:
	return [ '-ar', str(audio_sample_rate) ]


def set_audio_sample_size(audio_sample_size : int) -> Commands:
	if audio_sample_size == 16:
		return [ '-f', 's16le', '-acodec', 'pcm_s16le' ]
	if audio_sample_size == 32:
		return [ '-f', 's32le', '-acodec', 'pcm_s32le' ]
	return []


def set_audio_channel_total(audio_channel_total : int) -> Commands:
	return [ '-ac', str(audio_channel_total) ]


def set_audio_quality(audio_encoder : AudioEncoder, audio_quality : int) -> Commands:
	if audio_encoder == 'aac':
		audio_compression = round(10 - (audio_quality * 0.9))
		return [ '-q:a', str(audio_compression) ]
	if audio_encoder == 'libmp3lame':
		audio_compression = round(9 - (audio_quality * 0.9))
		return [ '-q:a', str(audio_compression) ]
	if audio_encoder in [ 'libopus', 'libvorbis' ]:
		audio_compression = round((100 - audio_quality) / 10)
		return [ '-q:a', str(audio_compression) ]
	return []


def set_audio_volume(audio_volume : int) -> Commands:
	return [ '-filter:a', 'volume=' + str(audio_volume / 100) ]


def set_video_encoder(video_encoder : str) -> Commands:
	return [ '-c:v', video_encoder ]


def copy_video_encoder() -> Commands:
	return set_video_encoder('copy')


def set_video_quality(video_encoder : VideoEncoder, video_quality : int) -> Commands:
	if video_encoder in [ 'libx264', 'libx265' ]:
		video_compression = round(51 - (video_quality * 0.51))
		return [ '-crf', str(video_compression) ]
	if video_encoder == 'libvpx-vp9':
		video_compression = round(63 - (video_quality * 0.63))
		return [ '-crf', str(video_compression) ]
	if video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		video_compression = round(51 - (video_quality * 0.51))
		return [ '-cq', str(video_compression) ]
	if video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		video_compression = round(51 - (video_quality * 0.51))
		return [ '-qp_i', str(video_compression), '-qp_p', str(video_compression) ]
	if video_encoder in [ 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox' ]:
		video_compression = round(51 - (video_quality * 0.51))
		return [ '-q:v', str(video_compression) ]
	return [ '-q:v', str(video_quality) ]


def set_video_preset(video_encoder : VideoEncoder, video_preset : VideoPreset) -> Commands:
	if video_encoder in [ 'libx264', 'libx265' ]:
		return [ '-preset', video_preset ]
	if video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		return [ '-preset', map_nvenc_preset(video_preset) ]
	if video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		return [ '-quality', map_amf_preset(video_preset) ]
	if video_encoder in [ 'h264_qsv', 'hevc_qsv' ]:
		return [ '-preset', map_qsv_preset(video_preset) ]
	return []


def set_video_colorspace(video_colorspace : str) -> Commands:
	return [ '-colorspace', video_colorspace ]


def set_video_fps(video_fps : Fps) -> Commands:
	return [ '-vf', 'framerate=fps=' + str(video_fps) ]


def set_video_duration(video_duration : Duration) -> Commands:
	return [ '-t', str(video_duration) ]


def ignore_video_stream() -> Commands:
	return [ '-vn' ]


def map_nvenc_preset(video_preset : VideoPreset) -> Optional[str]:
	if video_preset in [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast' ]:
		return 'fast'
	if video_preset == 'medium':
		return 'medium'
	if video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'slow'
	return None


def map_amf_preset(video_preset : VideoPreset) -> Optional[str]:
	if video_preset in [ 'ultrafast', 'superfast', 'veryfast' ]:
		return 'speed'
	if video_preset in [ 'faster', 'fast', 'medium' ]:
		return 'balanced'
	if video_preset in [ 'slow', 'slower', 'veryslow' ]:
		return 'quality'
	return None


def map_qsv_preset(video_preset : VideoPreset) -> Optional[str]:
	if video_preset in [ 'ultrafast', 'superfast', 'veryfast' ]:
		return 'veryfast'
	if video_preset in [ 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow' ]:
		return video_preset
	return None
