from _pytest.logging import LogCaptureFixture

from facefusion.cli_helper import create_table_parts, render_table


def test_render_table(caplog : LogCaptureFixture) -> None:
	render_table([ 'name', 'value' ],
	[
		[ 'face_swapper', 1 ],
		[ 'frame_enhancer', 10 ]
	])

	assert caplog.messages ==\
	[
		'+----------------+-------+',
		'| name           | value |',
		'+----------------+-------+',
		'| face_swapper   | 1     |',
		'| frame_enhancer | 10    |',
		'+----------------+-------+'
	]


def test_create_table_parts() -> None:
	assert create_table_parts([ 'name', 'value' ], []) == ('| {:<4} | {:<5} |', '+------+-------+')
	assert create_table_parts([ 'name', 'value' ],
	[
		[ 'face_swapper', 1 ],
		[ 'frame_enhancer', 1000000 ]
	]) == ('| {:<14} | {:<7} |', '+----------------+---------+')
