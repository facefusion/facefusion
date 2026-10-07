from facefusion.normalizer import normalize_color, normalize_fps, normalize_range, normalize_space


def test_normalize_color() -> None:
	assert normalize_color([ 0 ]) == (0, 0, 0, 255)
	assert normalize_color([ 0, 128 ]) == (0, 128, 0, 255)
	assert normalize_color([ 0, 128, 255 ]) == (0, 128, 255, 255)
	assert normalize_color([ 0, 128, 255, 0 ]) == (0, 128, 255, 0)
	assert normalize_color([]) is None
	assert normalize_color(None) is None
	assert normalize_color('invalid') is None


def test_normalize_space() -> None:
	assert normalize_space([ 1 ]) == (1, 1, 1, 1)
	assert normalize_space([ 1, 2 ]) == (1, 2, 1, 2)
	assert normalize_space([ 1, 2, 3 ]) == (1, 2, 3, 2)
	assert normalize_space([ 1, 2, 3, 4 ]) == (1, 2, 3, 4)
	assert normalize_space([ 1, 2, 3, 4, 5 ]) is None
	assert normalize_space([]) is None
	assert normalize_space(None) is None
	assert normalize_space('invalid') is None


def test_normalize_range() -> None:
	assert normalize_range(270, 0, 200) == (0, 200)
	assert normalize_range(270, 70, 270) == (70, 270)
	assert normalize_range(270, -10, None) == (0, 270)
	assert normalize_range(270, None, -10) == (0, 0)
	assert normalize_range(270, 280, None) == (270, 270)
	assert normalize_range(270, None, 280) == (0, 270)
	assert normalize_range(270, None, None) == (0, 270)


def test_normalize_fps() -> None:
	assert normalize_fps(-1.0) == 1.0
	assert normalize_fps(0.0) == 1.0
	assert normalize_fps(25.0) == 25.0
	assert normalize_fps(29.97) == 29.97
	assert normalize_fps(60.0) == 60.0
	assert normalize_fps(61.0) == 60.0
	assert normalize_fps(None) is None
	assert normalize_fps('invalid') is None
