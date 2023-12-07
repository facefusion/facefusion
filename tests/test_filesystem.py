from facefusion.filesystem import is_file, is_directory, is_image, are_images, is_video


def test_is_file() -> None:
	assert is_file('.assets/examples/source.jpg') is True
	assert is_file('.assets/examples') is False
	assert is_file('invalid') is False


def test_is_directory() -> None:
	assert is_directory('.assets/examples') is True
	assert is_directory('.assets/examples/source.jpg') is False
	assert is_directory('invalid') is False


def test_is_image() -> None:
	assert is_image('.assets/examples/source.jpg') is True
	assert is_image('.assets/examples/target-240p.mp4') is False
	assert is_image('invalid') is False


def test_are_images() -> None:
	assert are_images([ '.assets/examples/source.jpg' ]) is True
	assert are_images([ '.assets/examples/source.jpg', '.assets/examples/target-240p.mp4' ]) is False
	assert are_images([ 'invalid' ]) is False


def test_is_video() -> None:
	assert is_video('.assets/examples/target-240p.mp4') is True
	assert is_video('.assets/examples/source.jpg') is False
	assert is_video('invalid') is False
