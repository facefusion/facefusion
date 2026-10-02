import pytest

from facefusion.download import conditional_download
from facefusion.filesystem import copy_file
from facefusion.hash_helper import create_hash, get_hash_path, validate_hash
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, get_test_outputs_directory, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])

	prepare_test_output_directory()
	copy_file(get_test_example_file('source.jpg'), get_test_output_path('source.jpg'))
	copy_file(get_test_example_file('source.jpg'), get_test_output_path('source-padded.jpg'))
	copy_file(get_test_example_file('source.mp3'), get_test_output_path('source-invalid.mp3'))

	with open(get_test_output_path('source.hash'), 'w') as hash_file:
		hash_file.write('dbb11cca')

	with open(get_test_output_path('source-padded.hash'), 'w') as hash_file:
		hash_file.write('0dbb11cca0')

	with open(get_test_output_path('source-invalid.hash'), 'w') as hash_file:
		hash_file.write('invalid')


def test_create_hash() -> None:
	assert create_hash(bytes()) == '00000000'
	assert create_hash(bytes([ 1 ])) == 'a505df1b'
	assert create_hash('facefusion'.encode()) == '6afd0aae'


def test_validate_hash() -> None:
	assert validate_hash(get_test_output_path('source.jpg')) is True
	assert validate_hash(get_test_output_path('source-padded.jpg')) is False
	assert validate_hash(get_test_output_path('source-invalid.mp3')) is False
	assert validate_hash(get_test_example_file('source.jpg')) is False
	assert validate_hash('invalid') is False


def test_get_hash_path() -> None:
	assert get_hash_path(get_test_output_path('source.jpg')) == get_test_output_path('source.hash')
	assert get_hash_path(get_test_output_path('source-invalid.mp3')) == get_test_output_path('source-invalid.hash')
	assert get_hash_path(get_test_outputs_directory()) is None
	assert get_hash_path('invalid') is None
