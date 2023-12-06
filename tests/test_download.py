from facefusion.download import get_download_size, is_download_done


def test_get_download_size() -> None:
	assert get_download_size('https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4') == 191675
	assert get_download_size('https://github.com/facefusion/facefusion-assets/releases/download/examples/target-360p.mp4') == 370732
	assert get_download_size('invalid') == 0


def test_is_download_done() -> None:
	assert is_download_done('https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4', '.assets/examples/target-240p.mp4') is True
	assert is_download_done('https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4','invalid') is False
	assert is_download_done('invalid', 'invalid') is False
