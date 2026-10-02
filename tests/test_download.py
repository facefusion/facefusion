from unittest.mock import patch

import pytest

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download, conditional_download_hashes, conditional_download_sources, get_static_download_size, ping_static_url, resolve_download_url, resolve_download_url_by_provider, validate_hash_paths, validate_source_paths
from facefusion.filesystem import get_file_size, is_file, remove_file
from facefusion.hash_helper import create_hash
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, get_test_outputs_directory, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('download_providers', [ 'github' ])

	conditional_download('.assets/models',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.hash',
		'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx'
	])
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.hash'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	process_manager.end()
	prepare_test_output_directory()


def create_test_source(source_path : str, hash_content : str) -> None:
	source_buffer = bytes([ 1, 2, 3 ])

	with open(source_path, 'wb') as source_file:
		source_file.write(source_buffer)

	with open(source_path.replace('.onnx', '.hash'), 'w') as hash_file:
		hash_file.write(hash_content)


def test_conditional_download() -> None:
	remove_file(get_test_example_file('fairface.hash'))
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.hash'
	])

	assert get_file_size(get_test_example_file('fairface.hash')) == get_static_download_size('https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.hash')
	assert get_file_size(get_test_example_file('fairface.hash')) == 8


@pytest.mark.xfail(strict = True, raises = AssertionError, reason = 'TESTING_AND_FIXING.md #23')
def test_conditional_download_with_missing_url() -> None:
	conditional_download(get_test_outputs_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/invalid.jpg'
	])

	assert is_file(get_test_output_path('invalid.jpg')) is False


def test_get_static_download_size() -> None:
	assert get_static_download_size('https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx') == 85170772
	assert get_static_download_size('https://huggingface.co/facefusion/models-3.0.0/resolve/main/fairface.onnx') == 85170772
	assert get_static_download_size('invalid') == 0


def test_static_ping_url() -> None:
	assert ping_static_url('https://github.com') is True
	assert ping_static_url('https://huggingface.co') is True
	assert ping_static_url('invalid') is False


def test_conditional_download_hashes() -> None:
	hash_set =\
	{
		'fairface':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.hash',
			'path': '.assets/models/fairface.hash'
		}
	}

	assert conditional_download_hashes(hash_set) is True
	assert process_manager.is_pending() is True

	remove_file(get_test_example_file('fairface.hash'))
	hash_set =\
	{
		'fairface':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.hash',
			'path': get_test_example_file('fairface.hash')
		}
	}

	assert conditional_download_hashes(hash_set) is True
	assert is_file(get_test_example_file('fairface.hash')) is True

	hash_set =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': 'invalid'
		}
	}

	assert conditional_download_hashes(hash_set) is False


@pytest.mark.xfail(strict = True, raises = AssertionError, reason = 'TESTING_AND_FIXING.md #22')
def test_conditional_download_hashes_with_invalid_hash() -> None:
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
	source_set =\
	{
		'fairface':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx',
			'path': '.assets/models/fairface.onnx'
		}
	}

	assert conditional_download_sources(source_set) is True
	assert process_manager.is_pending() is True

	remove_file(get_test_example_file('yunet_2023_mar.onnx'))
	source_set =\
	{
		'yunet':
		{
			'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.4.0/yunet_2023_mar.onnx',
			'path': get_test_example_file('yunet_2023_mar.onnx')
		}
	}

	assert conditional_download_sources(source_set) is True
	assert is_file(get_test_example_file('yunet_2023_mar.onnx')) is True

	create_test_source(get_test_output_path('test-conditional-download-sources.onnx'), 'invalid')
	source_set =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': get_test_output_path('test-conditional-download-sources.onnx')
		}
	}

	assert conditional_download_sources(source_set) is False
	assert is_file(get_test_output_path('test-conditional-download-sources.onnx')) is False


@pytest.mark.xfail(strict = True, raises = AssertionError, reason = 'TESTING_AND_FIXING.md #22')
def test_conditional_download_sources_with_invalid_source() -> None:
	create_test_source(get_test_output_path('test-conditional-download-sources-with-invalid-source.onnx'), 'invalid')
	source_set =\
	{
		'invalid':
		{
			'url': 'invalid',
			'path': get_test_output_path('test-conditional-download-sources-with-invalid-source.onnx')
		}
	}

	assert conditional_download_sources(source_set) is False
	assert process_manager.is_pending() is True


def test_validate_hash_paths() -> None:
	assert validate_hash_paths([ '.assets/models/fairface.hash', 'invalid' ]) == ([ '.assets/models/fairface.hash' ], [ 'invalid' ])


def test_validate_source_paths() -> None:
	create_test_source(get_test_output_path('test-validate-source-paths-valid.onnx'), create_hash(bytes([ 1, 2, 3 ])))
	create_test_source(get_test_output_path('test-validate-source-paths-invalid.onnx'), 'invalid')

	assert validate_source_paths([ '.assets/models/fairface.onnx', get_test_output_path('test-validate-source-paths-valid.onnx') ]) == ([ '.assets/models/fairface.onnx', get_test_output_path('test-validate-source-paths-valid.onnx') ], [])
	assert validate_source_paths([ get_test_output_path('test-validate-source-paths-invalid.onnx'), 'invalid' ]) == ([], [ get_test_output_path('test-validate-source-paths-invalid.onnx'), 'invalid' ])


def test_resolve_download_url() -> None:
	state_manager.set_item('download_providers', [ 'github' ])

	assert resolve_download_url('models-3.0.0', 'fairface.onnx') == 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx'

	state_manager.set_item('download_providers', [ 'huggingface', 'github' ])

	assert resolve_download_url('models-3.0.0', 'fairface.onnx') == 'https://huggingface.co/facefusion/models-3.0.0/resolve/main/fairface.onnx'

	state_manager.set_item('download_providers', [])

	assert resolve_download_url('models-3.0.0', 'fairface.onnx') is None


def test_resolve_download_url_by_provider() -> None:
	assert resolve_download_url_by_provider('github', 'models-3.0.0', 'fairface.onnx') == 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/fairface.onnx'
	assert resolve_download_url_by_provider('huggingface', 'models-3.0.0', 'fairface.onnx') == 'https://huggingface.co/facefusion/models-3.0.0/resolve/main/fairface.onnx'

	with patch('facefusion.download.ping_static_url', return_value = False):
		assert resolve_download_url_by_provider('github', 'models-3.0.0', 'fairface.onnx') is None
