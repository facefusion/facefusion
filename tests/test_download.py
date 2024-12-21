from facefusion.download import get_static_download_size, ping_static_url, resolve_download_url_by_provider


def test_get_static_download_size() -> None:
	assert get_static_download_size('https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx') == 85170772
	assert get_static_download_size('https://huggingface.co/facefusion/models-3.0.0/resolve/main/fairface.onnx') == 85170772
	assert get_static_download_size('invalid') == 0


def test_static_ping_url() -> None:
	assert ping_static_url('https://github.com') is True
	assert ping_static_url('https://huggingface.co') is True
	assert ping_static_url('invalid') is False


def test_resolve_download_url_by_provider() -> None:
	assert resolve_download_url_by_provider('github', 'models-3.0.0', 'fairface.onnx') == 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx'
	assert resolve_download_url_by_provider('huggingface', 'models-3.0.0', 'fairface.onnx') == 'https://huggingface.co/facefusion/models-3.0.0/resolve/main/fairface.onnx'
