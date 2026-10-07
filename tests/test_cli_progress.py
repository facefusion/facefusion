import time

from _pytest.capture import CaptureFixture

from facefusion.cli_progress import create, render


def test_render_percent(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'percent', current = 1, total = 10) as progress:
		capsys.readouterr()
		render(progress)

		assert '10 %' in capsys.readouterr().out

		progress.total = 0
		capsys.readouterr()
		render(progress)

		assert '0 %' in capsys.readouterr().out


def test_render_frame(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'frame', current = 10, total = 100) as progress:
		progress.time_start = time.monotonic() - 10
		capsys.readouterr()
		render(progress)

		assert '1.0frame/s' in capsys.readouterr().out

		progress.time_start = time.monotonic() + 10
		capsys.readouterr()
		render(progress)

		assert '0.0frame/s' in capsys.readouterr().out


def test_render_download(capsys : CaptureFixture[str]) -> None:
	with create(unit = 'download', current = 10 * 1024, total = 20 * 1024 * 1024) as progress:
		progress.time_start = time.monotonic() - 10
		capsys.readouterr()
		render(progress)

		assert '1.0kb/s' in capsys.readouterr().out

		progress.current = 20 * 1024 * 1024
		capsys.readouterr()
		render(progress)

		assert '2.0mb/s' in capsys.readouterr().out

		progress.time_start = time.monotonic() + 10
		capsys.readouterr()
		render(progress)

		assert '0.0kb/s' in capsys.readouterr().out
