from shutil import which

from facefusion import ffmpeg_builder


def test_run() -> None:
	assert ffmpeg_builder.run([]) == [ which('ffmpeg'), '-loglevel', 'error' ]


def test_chain() -> None:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_progress()
	)

	assert commands == [ '-progress' ]


def test_stream_mode() -> None:
	assert ffmpeg_builder.set_stream_mode('udp') == [ '-f', 'mpegts' ]
	assert ffmpeg_builder.set_stream_mode('v4l2') == [ '-f', 'v4l2' ]


def test_select_frame_range() -> None:
	assert ffmpeg_builder.select_frame_range(0, None, 30) == [ '-vf', 'trim=start_frame=0,fps=30' ]
	assert ffmpeg_builder.select_frame_range(None, 100, 30) == [ '-vf', 'trim=end_frame=100,fps=30' ]
	assert ffmpeg_builder.select_frame_range(0, 100, 30) == [ '-vf', 'trim=start_frame=0:end_frame=100,fps=30' ]
	assert ffmpeg_builder.select_frame_range(None, None, 30) == [ '-vf', 'fps=30' ]


def test_audio_sample_size() -> None:
	assert ffmpeg_builder.set_audio_sample_size(16) == [ '-f', 's16le', '-acodec', 'pcm_s16le' ]
	assert ffmpeg_builder.set_audio_sample_size(32) == [ '-f', 's32le', '-acodec', 'pcm_s32le' ]
