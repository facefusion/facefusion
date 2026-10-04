from facefusion import process_manager
from facefusion.download import conditional_download_files, conditional_validate_files, get_static_download_size, ping_static_url, resolve_download_url_by_provider, validate_file
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


def test_conditional_download_files() -> None:
	hash_set : DownloadSet =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.hash',
			'path': '.assets/models/yunet_2023_mar.hash'
		}
	}
	source_set : DownloadSet =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx',
			'path': '.assets/models/yunet_2023_mar.onnx'
		}
	}
	invalid_set : DownloadSet =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': 'invalid'
		}
	}

	assert conditional_download_files(hash_set) is True
	assert process_manager.is_pending() is True
	assert conditional_download_files(source_set) is True
	assert process_manager.is_pending() is True
	assert conditional_download_files(invalid_set) is False
	assert process_manager.is_pending() is True


def test_conditional_validate_files() -> None:
	file_set : DownloadSet =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx',
			'path': '.assets/models/yunet_2023_mar.onnx'
		}
	}
	invalid_set : DownloadSet =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': 'invalid'
		}
	}

	assert conditional_validate_files(file_set) is True
	assert conditional_validate_files(invalid_set) is False


def test_validate_file() -> None:
	assert validate_file('.assets/models/yunet_2023_mar.hash') is True
	assert validate_file('.assets/models/yunet_2023_mar.onnx') is True
	assert validate_file('invalid.hash') is False
	assert validate_file('invalid') is False


def test_resolve_download_url_by_provider() -> None:
	assert resolve_download_url_by_provider('github', 'models-3.4.0', 'yunet_2023_mar.onnx') == 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx'
	assert resolve_download_url_by_provider('huggingface', 'models-3.4.0', 'yunet_2023_mar.onnx') == 'https://huggingface.co/facefusion/models-3.4.0/resolve/main/yunet_2023_mar.onnx'
