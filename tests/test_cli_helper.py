from _pytest.logging import LogCaptureFixture

from facefusion.cli_helper import render_table


def test_render_table(caplog : LogCaptureFixture) -> None:
	render_table([ 'name', 'value' ],
	[
		[ 'alpha', 1.0 ],
		[ 'beta', 2.0 ]
	])

	assert caplog.messages[0] == '+-------+-------+'
	assert caplog.messages[1] == '| name  | value |'
	assert caplog.messages[2] == '+-------+-------+'
	assert caplog.messages[3] == '| alpha | 1.0   |'
	assert caplog.messages[4] == '| beta  | 2.0   |'
	assert caplog.messages[5] == '+-------+-------+'
