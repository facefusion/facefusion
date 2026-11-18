from _pytest.logging import LogCaptureFixture

from facefusion.clis.cli_table import render


def test_render(caplog : LogCaptureFixture) -> None:
	render([ 'name', 'value' ],
	[
		[ 'alpha', 1.0 ],
		[ 'beta', 2.0 ]
	])

	assert caplog.messages[0] == '┌───────┬───────┐'
	assert caplog.messages[1] == '│ name  │ value │'
	assert caplog.messages[2] == '├───────┼───────┤'
	assert caplog.messages[3] == '│ alpha │ 1.0   │'
	assert caplog.messages[4] == '│ beta  │ 2.0   │'
	assert caplog.messages[5] == '└───────┴───────┘'
