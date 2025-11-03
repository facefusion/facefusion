import itertools
import shutil
from typing import List, Optional

import numpy

from facefusion.filesystem import get_file_format
from facefusion.types import AudioEncoder, Command, CommandSet, Duration, Fps, StreamMode, VideoEncoder, VideoPreset


def run(commands : List[Command]) -> List[Command]:
	return [ shutil.which('ffmpeg'), '-loglevel', 'error' ] + commands


def chain(*commands : List[Command]) -> List[Command]:
	return list(itertools.chain(*commands))


def concat(*__commands__ : List[Command]) -> List[Command]:
	commands = []
	command_set : CommandSet = {}

	for command in __commands__:
		for argument, value in zip(command[::2], command[1::2]):
			command_set.setdefault(argument, []).append(value)

	for argument, values in command_set.items():
		commands.append(argument)
		commands.append(','.join(values))

	return commands


def get_encoders() -> List[Command]:
	return [ '-encoders' ]


def set_hardware_accelerator(value : str) -> List[Command]:
	return [ '-hwaccel', value ]


def set_progress() -> List[Command]:
	return [ '-progress' ]


def set_input(input_path : str) -> List[Command]:
	return [ '-i', input_path ]


def set_input_fps(input_fps : Fps) -> List[Command]:
	return [ '-r', str(input_fps)]


def set_output(output_path : str) -> List[Command]:
	return [ output_path ]


def force_output(output_path : str) -> List[Command]:
	return [ '-y', output_path ]


def cast_stream() -> List[Command]:
	return [ '-' ]


def set_stream_mode(stream_mode : StreamMode) -> List[Command]:
	if stream_mode == 'udp':
		return [ '-f', 'mpegts' ]
	if stream_mode == 'v4l2':
		return [ '-f', 'v4l2' ]
	return []


def set_stream_quality(stream_quality : int) -> List[Command]:
	return [ '-b:v', str(stream_quality) + 'k' ]


def unsafe_concat() -> List[Command]:
	return [ '-f', 'concat', '-safe', '0' ]


def set_pixel_format(video_encoder : VideoEncoder) -> List[Command]:
	if video_encoder == 'rawvideo':
		return [ '-pix_fmt', 'rgb24' ]
	if video_encoder == 'libvpx-vp9':
		return [ '-pix_fmt', 'yuva420p' ]
	return [ '-pix_fmt', 'yuv420p' ]


def set_frame_quality(frame_quality : int) -> List[Command]:
	return [ '-q:v', str(frame_quality) ]


def select_frame_range(frame_start : int, frame_end : int, video_fps : Fps) -> List[Command]:
	if isinstance(frame_start, int) and isinstance(frame_end, int):
		return [ '-vf', 'trim=start_frame=' + str(frame_start) + ':end_frame=' + str(frame_end) + ',fps=' + str(video_fps) ]
	if isinstance(frame_start, int):
		return [ '-vf', 'trim=start_frame=' + str(frame_start) + ',fps=' + str(video_fps) ]
	if isinstance(frame_end, int):
		return [ '-vf', 'trim=end_frame=' + str(frame_end) + ',fps=' + str(video_fps) ]
	return [ '-vf', 'fps=' + str(video_fps) ]


def prevent_frame_drop() -> List[Command]:
	return [ '-vsync', '0' ]


def select_media_range(frame_start : int, frame_end : int, media_fps : Fps) -> List[Command]:
	commands = []

	if isinstance(frame_start, int):
		commands.extend([ '-ss', str(frame_start / media_fps) ])
	if isinstance(frame_end, int):
		commands.extend([ '-to', str(frame_end / media_fps) ])
	return commands


def select_media_stream(media_stream : str) -> List[Command]:
	return [ '-map', media_stream ]


def set_media_resolution(video_resolution : str) -> List[Command]:
	return [ '-s', video_resolution ]


def set_image_quality(image_path : str, image_quality : int) -> List[Command]:
	if get_file_format(image_path) == 'webp':
		return [ '-q:v', str(image_quality) ]

	image_compression = round(31 - (image_quality * 0.31))
	return [ '-q:v', str(image_compression) ]


def set_audio_encoder(audio_codec : str) -> List[Command]:
	return [ '-c:a', audio_codec ]


def copy_audio_encoder() -> List[Command]:
	return set_audio_encoder('copy')


def set_audio_sample_rate(audio_sample_rate : int) -> List[Command]:
	return [ '-ar', str(audio_sample_rate) ]


def set_audio_sample_size(audio_sample_size : int) -> List[Command]:
	if audio_sample_size == 16:
		return [ '-f', 's16le' ]
	if audio_sample_size == 32:
		return [ '-f', 's32le' ]
	return []


def set_audio_channel_total(audio_channel_total : int) -> List[Command]:
	return [ '-ac', str(audio_channel_total) ]


def set_audio_quality(audio_encoder : AudioEncoder, audio_quality : int) -> List[Command]:
	if audio_encoder == 'aac':
		audio_compression = numpy.round(numpy.interp(audio_quality, [ 0, 100 ], [ 0.1, 2.0 ]), 1).astype(float).item()
		return [ '-q:a', str(audio_compression) ]
	if audio_encoder == 'libmp3lame':
		audio_compression = numpy.round(numpy.interp(audio_quality, [ 0, 100 ], [ 9, 0 ])).astype(int).item()
		return [ '-q:a', str(audio_compression) ]
	if audio_encoder == 'libopus':
		audio_bit_rate = numpy.round(numpy.interp(audio_quality, [ 0, 100 ], [ 64, 256 ])).astype(int).item()
		return [ '-b:a', str(audio_bit_rate) + 'k' ]
	if audio_encoder == 'libvorbis':
		audio_compression = numpy.round(numpy.interp(audio_quality, [ 0, 100 ], [ -1, 10 ]), 1).astype(float).item()
		return [ '-q:a', str(audio_compression) ]
	return []


def set_audio_volume(audio_volume : int) -> List[Command]:
	return [ '-filter:a', 'volume=' + str(audio_volume / 100) ]


def set_video_encoder(video_encoder : str) -> List[Command]:
	return [ '-c:v', video_encoder ]


def copy_video_encoder() -> List[Command]:
	return set_video_encoder('copy')


def set_video_quality(video_encoder : VideoEncoder, video_quality : int) -> List[Command]:
	if video_encoder in [ 'libx264', 'libx264rgb', 'libx265' ]:
		video_compression = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 51, 0 ])).astype(int).item()
		return [ '-crf', str(video_compression) ]
	if video_encoder == 'libvpx-vp9':
		video_compression = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 63, 0 ])).astype(int).item()
		return [ '-crf', str(video_compression) ]
	if video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		video_compression = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 51, 0 ])).astype(int).item()
		return [ '-cq', str(video_compression) ]
	if video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		video_compression = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 51, 0 ])).astype(int).item()
		return [ '-qp_i', str(video_compression), '-qp_p', str(video_compression), '-qp_b', str(video_compression) ]
	if video_encoder in [ 'h264_qsv', 'hevc_qsv' ]:
		video_compression = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 51, 0 ])).astype(int).item()
		return [ '-qp', str(video_compression) ]
	if video_encoder in [ 'h264_videotoolbox', 'hevc_videotoolbox' ]:
		video_bit_rate = numpy.round(numpy.interp(video_quality, [ 0, 100 ], [ 1024, 50512 ])).astype(int).item()
		return [ '-b:v', str(video_bit_rate) + 'k' ]
	return []


def set_video_preset(video_encoder : VideoEncoder, video_preset : VideoPreset) -> List[Command]:
	if video_encoder in [ 'libx264', 'libx264rgb', 'libx265' ]:
		return [ '-preset', video_preset ]
	if video_encoder in [ 'h264_nvenc', 'hevc_nvenc' ]:
		return [ '-preset', map_nvenc_preset(video_preset) ]
	if video_encoder in [ 'h264_amf', 'hevc_amf' ]:
		return [ '-quality', map_amf_preset(video_preset) ]
	if video_encoder in [ 'h264_qsv', 'hevc_qsv' ]:
		return [ '-preset', map_qsv_preset(video_preset) ]
	return []


def set_video_fps(video_fps : Fps) -> List[Command]:
	return [ '-vf', 'fps=' + str(video_fps) ]


def set_video_duration(video_duration : Duration) -> List[Command]:
	return [ '-t', str(video_duration) ]


def keep_video_alpha(video_encoder : VideoEncoder) -> List[Command]:
	if video_encoder == 'libvpx-vp9':
		return [ '-vf', 'format=yuva420p' ]
	return []


def capture_video() -> List[Command]:
	return [ '-f', 'rawvideo', '-pix_fmt', 'rgb24' ]


def ignore_video_stream() -> List[Command]:
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
