from shutil import which

from facefusion import ffmpeg_builder


def test_run() -> None:
	assert ffmpeg_builder.run([]) == [ which('ffmpeg'), '-loglevel', 'error' ]


def test_chain() -> None:
	commands = ffmpeg_builder.chain(
		ffmpeg_builder.set_progress()
	)

	assert ffmpeg_builder.chain(commands) == [ '-progress' ]
