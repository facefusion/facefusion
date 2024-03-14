import platform

from facefusion.normalizer import normalize_output_path, normalize_padding, normalize_fps


def test_normalize_output_path() -> None:
	if platform.system().lower() == 'linux' or platform.system().lower() == 'darwin':
		assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/examples/target-240p.mp4') == '.assets/examples/target-240p.mp4'
		assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/examples').startswith('.assets/examples/target-240p')
		assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/examples').endswith('.mp4')
		assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/examples/output.mp4') == '.assets/examples/output.mp4'
	assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/examples/invalid') is None
	assert normalize_output_path('.assets/examples/target-240p.mp4', '.assets/invalid/output.mp4') is None
	assert normalize_output_path('.assets/examples/target-240p.mp4', 'invalid') is None
	assert normalize_output_path('.assets/examples/target-240p.mp4', None) is None
	assert normalize_output_path(None, '.assets/examples/output.mp4') is None


def test_normalize_padding() -> None:
	assert normalize_padding([ 0, 0, 0, 0 ]) == (0, 0, 0, 0)
	assert normalize_padding([ 1 ]) == (1, 1, 1, 1)
	assert normalize_padding([ 1, 2 ]) == (1, 2, 1, 2)
	assert normalize_padding([ 1, 2, 3 ]) == (1, 2, 3, 2)
	assert normalize_padding(None) is None


def test_normalize_fps() -> None:
	assert normalize_fps(0.0) == 1.0
	assert normalize_fps(25.0) == 25.0
	assert normalize_fps(61.0) == 60.0
	assert normalize_fps(None) is None
