from facefusion.sanitizer import sanitize_int_range


def test_sanitize_int_range() -> None:
	assert sanitize_int_range(0, [ 0, 1, 2 ]) == 0
	assert sanitize_int_range(2, [0, 1, 2]) == 2
	assert sanitize_int_range(-1, [ 0, 1 ]) == 0
	assert sanitize_int_range(3, [ 0, 1 ]) == 0
