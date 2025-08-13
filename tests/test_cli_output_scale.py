import subprocess
import sys

import pytest

from facefusion.vision import detect_video_resolution, detect_image_resolution
from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def test_original_scale_on_image() -> None:
	target_file_path = get_test_example_file('target-240p.jpg')
	output_file_path = get_test_output_file('test-original-scale-on-image.jpg')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', target_file_path, '-o', output_file_path, '--output-image-scale', '1.0' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-original-scale-on-image.jpg') is True
	assert detect_image_resolution(target_file_path) == detect_image_resolution(output_file_path)


def test_half_scale_on_image() -> None:
	output_file_path = get_test_output_file('test-half-scale-on-image.jpg')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', get_test_example_file('target-240p.jpg'), '-o', output_file_path, '--output-image-scale', '0.5' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-half-scale-on-image.jpg') is True
	assert detect_image_resolution(output_file_path) == (212, 112)


def test_double_scale_on_image() -> None:
	output_file_path = get_test_output_file('test-double-scale-on-image.jpg')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', get_test_example_file('target-240p.jpg'), '-o', output_file_path, '--output-image-scale', '2.0' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-double-scale-on-image.jpg') is True
	assert detect_image_resolution(output_file_path) == (852, 452)


def test_false_scale_on_image() -> None:
	target_file_path = get_test_example_file('target-240p.jpg')
	output_file_path = get_test_output_file('test-false-scale-on-image.jpg')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', target_file_path, '-o', output_file_path, '--output-image-scale', '8.0' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-false-scale-on-image.jpg') is True
	assert detect_image_resolution(output_file_path) == (3408, 1808)


def test_original_scale_to_video() -> None:
	target_file_path = get_test_example_file('target-240p.mp4')
	output_file_path = get_test_output_file('test-original-scale-on-video.mp4')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', target_file_path, '-o', output_file_path, '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-original-scale-on-video.mp4') is True
	assert detect_video_resolution(target_file_path) == detect_video_resolution(output_file_path)


def test_half_scale_to_video() -> None:
	output_file_path = get_test_output_file('test-half-scale-on-video.mp4')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', get_test_example_file('target-240p.mp4'), '-o', output_file_path, '--trim-frame-end', '1', '--output-video-scale', '0.5' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-half-scale-on-video.mp4') is True
	assert detect_video_resolution(output_file_path) == (212, 112)


def test_double_scale_to_video() -> None:
	output_file_path = get_test_output_file('test-double-scale-on-video.mp4')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'frame_enhancer', '-t', get_test_example_file('target-240p.mp4'), '-o', output_file_path, '--trim-frame-end', '1', '--output-video-scale', '2.0' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-double-scale-on-video.mp4') is True
	assert detect_video_resolution(output_file_path) == (852, 452)


def test_false_scale_to_video() -> None:
	output_file_path = get_test_output_file('test-false-scale-on-video.mp4')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', output_file_path, '--trim-frame-end', '1', '--output-video-scale', '8.0' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-false-scale-on-video.mp4') is True
	assert detect_video_resolution(output_file_path) == (3408, 1808)
