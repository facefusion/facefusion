import os.path

import pytest

from facefusion.download import conditional_download
from facefusion.filesystem import are_audios, are_images, are_videos, copy_file, create_directory, filter_audio_paths, filter_image_paths, get_file_extension, get_file_format, get_file_name, get_file_size, has_audio, has_image, has_video, in_directory, is_audio, is_directory, is_file, is_image, is_video, move_directory, move_file, remove_directory, remove_file, resolve_file_paths, resolve_file_pattern, resolve_relative_path
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, get_test_outputs_directory, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_get_file_size() -> None:
	assert get_file_size(get_test_example_file('source.jpg')) == 549458
	assert get_file_size('invalid') == 0


def test_get_file_name() -> None:
	assert get_file_name(get_test_example_file('source.jpg')) == 'source'
	assert get_file_name('target-240p.mp4') == 'target-240p'
	assert get_file_name('target.tar.gz') == 'target.tar'
	assert get_file_name('invalid') == 'invalid'
	assert get_file_name(get_test_examples_directory() + os.sep) is None


def test_get_file_extension() -> None:
	assert get_file_extension('source.jpg') == '.jpg'
	assert get_file_extension('source.mp3') == '.mp3'
	assert get_file_extension('source.JPG') == '.jpg'
	assert get_file_extension('invalid') is None


def test_get_file_format() -> None:
	assert get_file_format('source.jpg') == 'jpeg'
	assert get_file_format('source.jpeg') == 'jpeg'
	assert get_file_format('source.JPG') == 'jpeg'
	assert get_file_format('source.tif') == 'tiff'
	assert get_file_format('source.tiff') == 'tiff'
	assert get_file_format('target.mpg') == 'mpeg'
	assert get_file_format('source.mp3') == 'mp3'
	assert get_file_format('target.mp4') == 'mp4'
	assert get_file_format('invalid') is None


def test_is_file() -> None:
	assert is_file(get_test_example_file('source.jpg')) is True
	assert is_file(get_test_examples_directory()) is False
	assert is_file('invalid') is False


def test_is_audio() -> None:
	assert is_audio(get_test_example_file('source.mp3')) is True
	assert is_audio(get_test_example_file('source.jpg')) is False
	assert is_audio('invalid') is False


def test_has_audio() -> None:
	assert has_audio([ get_test_example_file('source.mp3') ]) is True
	assert has_audio([ get_test_example_file('source.mp3'), get_test_example_file('source.jpg') ]) is True
	assert has_audio([ get_test_example_file('source.jpg'), get_test_example_file('source.jpg') ]) is False
	assert has_audio([ 'invalid' ]) is False
	assert has_audio([]) is False


def test_are_audios() -> None:
	assert are_audios([ get_test_example_file('source.mp3') ]) is True
	assert are_audios([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) is True
	assert are_audios([ get_test_example_file('source.mp3'), get_test_example_file('source.jpg') ]) is False
	assert are_audios([ 'invalid' ]) is False
	assert are_audios([]) is False


def test_is_image() -> None:
	assert is_image(get_test_example_file('source.jpg')) is True
	assert is_image(get_test_example_file('target-240p.mp4')) is False
	assert is_image('invalid') is False


def test_has_image() -> None:
	assert has_image([ get_test_example_file('source.jpg') ]) is True
	assert has_image([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) is True
	assert has_image([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) is False
	assert has_image([ 'invalid' ]) is False
	assert has_image([]) is False


def test_are_images() -> None:
	assert are_images([ get_test_example_file('source.jpg') ]) is True
	assert are_images([ get_test_example_file('source.jpg'), get_test_example_file('source.jpg') ]) is True
	assert are_images([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) is False
	assert are_images([ 'invalid' ]) is False
	assert are_images([]) is False


def test_is_video() -> None:
	assert is_video(get_test_example_file('target-240p.mp4')) is True
	assert is_video(get_test_example_file('source.jpg')) is False
	assert is_video('invalid') is False


def test_has_video() -> None:
	assert has_video([ get_test_example_file('target-240p.mp4') ]) is True
	assert has_video([ get_test_example_file('target-240p.mp4'), get_test_example_file('source.mp3') ]) is True
	assert has_video([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) is False
	assert has_video([ 'invalid' ]) is False
	assert has_video([]) is False


def test_are_videos() -> None:
	assert are_videos([ get_test_example_file('target-240p.mp4') ]) is True
	assert are_videos([ get_test_example_file('target-240p.mp4'), get_test_example_file('target-240p.mp4') ]) is True
	assert are_videos([ get_test_example_file('target-240p.mp4'), get_test_example_file('source.jpg') ]) is False
	assert are_videos([ 'invalid' ]) is False
	assert are_videos([]) is False


def test_filter_audio_paths() -> None:
	assert filter_audio_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) == [ get_test_example_file('source.mp3') ]
	assert filter_audio_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.jpg') ]) == []
	assert filter_audio_paths([ 'invalid' ]) == []
	assert filter_audio_paths([]) == []


def test_filter_image_paths() -> None:
	assert filter_image_paths([ get_test_example_file('source.jpg'), get_test_example_file('source.mp3') ]) == [ get_test_example_file('source.jpg') ]
	assert filter_image_paths([ get_test_example_file('source.mp3'), get_test_example_file('source.mp3') ]) == []
	assert filter_image_paths([ 'invalid' ]) == []
	assert filter_image_paths([]) == []


def test_copy_file() -> None:
	output_path = get_test_output_path('test-copy-file.jpg')

	assert copy_file(get_test_example_file('source.jpg'), output_path) is True
	assert get_file_size(output_path) == 549458
	assert is_file(get_test_example_file('source.jpg')) is True
	assert copy_file('invalid', output_path) is False


def test_move_file() -> None:
	file_path = get_test_output_path('test-move-file.jpg')
	output_path = get_test_output_path('test-move-file-moved.jpg')
	copy_file(get_test_example_file('source.jpg'), file_path)

	assert move_file(file_path, output_path) is True
	assert is_file(file_path) is False
	assert get_file_size(output_path) == 549458
	assert move_file(file_path, output_path) is False


@pytest.mark.xfail(strict = True, raises = FileNotFoundError, reason = 'TESTING_AND_FIXING.md #6')
def test_move_file_to_missing_directory() -> None:
	file_path = get_test_output_path('test-move-file-to-missing-directory.jpg')
	copy_file(get_test_example_file('source.jpg'), file_path)

	assert move_file(file_path, get_test_output_path('invalid/test-move-file-to-missing-directory.jpg')) is False
	assert is_file(file_path) is True


def test_remove_file() -> None:
	file_path = get_test_output_path('test-remove-file.jpg')
	copy_file(get_test_example_file('source.jpg'), file_path)

	assert remove_file(file_path) is True
	assert is_file(file_path) is False
	assert remove_file(file_path) is False
	assert remove_file(get_test_outputs_directory()) is False


def test_resolve_file_paths() -> None:
	file_paths = resolve_file_paths(get_test_examples_directory())

	for file_path in file_paths:
		assert file_path == get_test_example_file(file_path)

	for file_name in [ 'test-resolve-file-paths-2.jpg', '.test-resolve-file-paths.jpg', '__test-resolve-file-paths.jpg', 'test-resolve-file-paths-1.jpg' ]:
		copy_file(get_test_example_file('source.jpg'), get_test_output_path(file_name))

	assert resolve_file_paths(get_test_outputs_directory()) ==\
	[
		get_test_output_path('test-resolve-file-paths-1.jpg'),
		get_test_output_path('test-resolve-file-paths-2.jpg')
	]
	assert resolve_file_paths(get_test_example_file('source.jpg')) == []
	assert resolve_file_paths('invalid') == []


def test_resolve_file_pattern() -> None:
	for file_name in [ 'test-resolve-file-pattern-2.jpg', 'test-resolve-file-pattern-1.jpg', 'test-resolve-file-pattern.mp3' ]:
		copy_file(get_test_example_file('source.jpg'), get_test_output_path(file_name))

	assert resolve_file_pattern(get_test_output_path('*.jpg')) ==\
	[
		get_test_output_path('test-resolve-file-pattern-1.jpg'),
		get_test_output_path('test-resolve-file-pattern-2.jpg')
	]
	assert resolve_file_pattern(get_test_output_path('*.png')) == []
	assert resolve_file_pattern(os.path.join('invalid', '*.jpg')) == []
	assert resolve_file_pattern('invalid') == []


def test_create_directory() -> None:
	create_directory_path = os.path.join(get_test_outputs_directory(), 'create_directory')

	assert create_directory(create_directory_path) is True
	assert create_directory(get_test_example_file('source.jpg')) is False


def test_move_directory() -> None:
	directory_path = os.path.join(get_test_outputs_directory(), 'move_directory')
	move_path = os.path.join(get_test_outputs_directory(), 'move_directory_moved')
	create_directory(directory_path)
	copy_file(get_test_example_file('source.jpg'), os.path.join(directory_path, 'source.jpg'))

	assert move_directory(directory_path, move_path) is True
	assert is_directory(directory_path) is False
	assert is_file(os.path.join(move_path, 'source.jpg')) is True
	assert move_directory(directory_path, move_path) is False
	assert move_directory(get_test_example_file('source.jpg'), move_path) is False


def test_remove_directory() -> None:
	remove_directory_path = os.path.join(get_test_outputs_directory(), 'remove_directory')
	create_directory(remove_directory_path)

	assert remove_directory(remove_directory_path) is True
	assert remove_directory(get_test_example_file('source.jpg')) is False
	assert remove_directory('invalid') is False


def test_is_directory() -> None:
	assert is_directory(get_test_examples_directory()) is True
	assert is_directory(get_test_example_file('source.jpg')) is False
	assert is_directory('invalid') is False


def test_in_directory() -> None:
	assert in_directory(get_test_example_file('source.jpg')) is True
	assert in_directory(get_test_example_file('invalid.jpg')) is True
	assert in_directory(get_test_examples_directory()) is False
	assert in_directory('source.jpg') is False
	assert in_directory('invalid') is False


def test_resolve_relative_path() -> None:
	assert resolve_relative_path('../.assets') == os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.assets'))
	assert resolve_relative_path('filesystem.py') == os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'facefusion', 'filesystem.py'))
