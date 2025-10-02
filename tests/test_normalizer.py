from facefusion.normalizer import normalize_fps, normalize_space


def test_normalize_space() -> None:
	assert normalize_space([ 0, 0, 0, 0 ]) == (0, 0, 0, 0)
	assert normalize_space([ 1 ]) == (1, 1, 1, 1)
	assert normalize_space([ 1, 2 ]) == (1, 2, 1, 2)
	assert normalize_space([ 1, 2, 3 ]) == (1, 2, 3, 2)
	assert normalize_space(None) is None


def test_normalize_fps() -> None:
	assert normalize_fps(0.0) == 1.0
	assert normalize_fps(25.0) == 25.0
	assert normalize_fps(61.0) == 60.0
	assert normalize_fps(None) is None
