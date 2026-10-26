from facefusion import process_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, get_static_download_size, ping_static_url, resolve_download_url_by_provider
from facefusion.types import DownloadSet


def test_get_static_download_size() -> None:
	assert get_static_download_size('https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx') == 232475
	assert get_static_download_size('https://huggingface.co/facefusion/models-3.4.0/resolve/main/yunet_2023_mar.onnx') == 232475
	assert get_static_download_size('https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/invalid.onnx') == 0
	assert get_static_download_size('invalid') == 0


def test_static_ping_url() -> None:
	assert ping_static_url('https://github.com') is True
	assert ping_static_url('https://huggingface.co') is True
	assert ping_static_url('invalid') is False


def test_conditional_download_hashes() -> None:
	hash_set : DownloadSet =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.hash',
			'path': '.assets/models/yunet_2023_mar.hash'
		}
	}

	assert conditional_download_hashes(hash_set) is True
	assert process_manager.is_pending() is True

	hash_set =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': 'invalid'
		}
	}

	assert conditional_download_hashes(hash_set) is False
	assert process_manager.is_pending() is True


def test_conditional_download_sources() -> None:
	source_set : DownloadSet =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx',
			'path': '.assets/models/yunet_2023_mar.onnx'
		}
	}

	assert conditional_download_sources(source_set) is True
	assert process_manager.is_pending() is True

	source_set =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': 'invalid'
		}
	}

	assert conditional_download_sources(source_set) is False
	assert process_manager.is_pending() is True


def test_resolve_download_url_by_provider() -> None:
	assert resolve_download_url_by_provider('github', 'models-3.4.0', 'yunet_2023_mar.onnx') == 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx'
	assert resolve_download_url_by_provider('huggingface', 'models-3.4.0', 'yunet_2023_mar.onnx') == 'https://huggingface.co/facefusion/models-3.4.0/resolve/main/yunet_2023_mar.onnx'
