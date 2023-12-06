import platform

from facefusion.normalizer import normalize_output_path, normalize_padding


def test_normalize_output_path() -> None:
	if platform.system().lower() != 'windows':
		assert normalize_output_path([ '.assets/examples/source.jpg' ], None, '.assets/examples/target-240p.mp4') == '.assets/examples/target-240p.mp4'
		assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/examples/target-240p.mp4') == '.assets/examples/target-240p.mp4'
		assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/examples') == '.assets/examples/target-240p.mp4'
		assert normalize_output_path([ '.assets/examples/source.jpg' ], '.assets/examples/target-240p.mp4', '.assets/examples') == '.assets/examples/source-target-240p.mp4'
		assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/examples/output.mp4') == '.assets/examples/output.mp4'
		assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/output.mov') == '.assets/output.mp4'
	assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/examples/invalid') is None
	assert normalize_output_path(None, '.assets/examples/target-240p.mp4', '.assets/invalid/output.mp4') is None
	assert normalize_output_path(None, '.assets/examples/target-240p.mp4', 'invalid') is None
	assert normalize_output_path([ '.assets/examples/source.jpg' ], '.assets/examples/target-240p.mp4', None) is None


def test_normalize_padding() -> None:
	assert normalize_padding([ 0, 0, 0, 0 ]) == (0, 0, 0, 0)
	assert normalize_padding([ 1 ]) == (1, 1, 1, 1)
	assert normalize_padding([ 1, 2 ]) == (1, 2, 1, 2)
	assert normalize_padding([ 1, 2, 3 ]) == (1, 2, 3, 2)
	assert normalize_padding(None) is None
