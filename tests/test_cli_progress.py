import time

from _pytest.capture import CaptureFixture

from facefusion import choices
from facefusion.cli_progress import count, create, render, resolve_download, resolve_frame, resolve_percent, seek, set_description, set_title, update


def test_create(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'percent', total = 4) as progress:
		progress.set_title('title')
		progress.set_description('description')
		progress.update()

		assert progress.current == 1

	assert progress.current == 4
	assert progress.unit == 'percent'
	assert '100 %' in capsys.readouterr().out


def test_set_title() -> None:
	with create() as progress:
		set_title(progress, 'title')

	assert progress.title == 'title'


def test_set_description() -> None:
	with create() as progress:
		set_description(progress, 'description')

	assert progress.description == 'description'


def test_count() -> None:
	with create() as progress:
		count(progress, [ 1, 2, 3 ])

		assert progress.total == 3


def test_update() -> None:
	with create(total = 3) as progress:
		update(progress)
		update(progress)

		assert progress.current == 2


def test_seek(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'percent', total = 10) as progress:
		capsys.readouterr()
		seek(progress, 5)

		assert progress.current == 5
		assert '50 %' in capsys.readouterr().out

		seek(progress, 6)

		assert progress.current == 6
		assert capsys.readouterr().out == ''


def test_render(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'percent', current = 1, total = 4) as progress:
		progress.set_title('title')
		progress.set_description('description')
		capsys.readouterr()
		render(progress)
		output = capsys.readouterr().out

		assert output.startswith(choices.progress_action_set.get('cursor_start') + 'title ') is True
		assert output.endswith(' 25 % | description' + choices.progress_action_set.get('erase_line')) is True

	with create(unit = 'download', total = 0) as progress:
		capsys.readouterr()
		render(progress)

		assert 'kb/s' in capsys.readouterr().out


def test_resolve_percent() -> None:
	with create(unit = 'percent', current = 1, total = 3) as progress:
		assert resolve_percent(progress) == '33 %'

	with create(unit = 'percent', total = 0) as progress:
		assert resolve_percent(progress) == '0 %'


def test_resolve_frame() -> None:
	with create(current = 10) as progress:
		progress.time_start = time.monotonic() - 10

		assert resolve_frame(progress) == '1.0frame/s'

		progress.time_start = time.monotonic() + 10

		assert resolve_frame(progress) == '0.0frame/s'


def test_resolve_download() -> None:
	with create(unit = 'download', current = 20 * 1024 * 1024) as progress:
		progress.time_start = time.monotonic() - 10

		assert resolve_download(progress) == '2.0mb/s'

		progress.current = 10 * 1024

		assert resolve_download(progress) == '1.0kb/s'

		progress.time_start = time.monotonic() + 10

		assert resolve_download(progress) == '0.0kb/s'
