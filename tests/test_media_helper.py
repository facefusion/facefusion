from facefusion.media_helper import restrict_trim_frame


def test_restrict_trim_frame() -> None:
	assert restrict_trim_frame(270, None, None) == (0, 270)
	assert restrict_trim_frame(270, 0, 270) == (0, 270)
	assert restrict_trim_frame(270, 124, 224) == (124, 224)
	assert restrict_trim_frame(270, 124, None) == (124, 270)
	assert restrict_trim_frame(270, None, 224) == (0, 224)
	assert restrict_trim_frame(270, -10, 300) == (0, 270)
	assert restrict_trim_frame(270, -10, None) == (0, 270)
	assert restrict_trim_frame(270, None, 300) == (0, 270)
	assert restrict_trim_frame(270, 300, None) == (270, 270)
	assert restrict_trim_frame(270, None, -10) == (0, 0)
	assert restrict_trim_frame(270, 269, 270) == (269, 270)
	assert restrict_trim_frame(270, 270, 271) == (270, 270)
	assert restrict_trim_frame(0, 124, 224) == (0, 0)
	assert restrict_trim_frame(0, None, None) == (0, 0)
	assert restrict_trim_frame(270, 'invalid', 'invalid') == (0, 270)
