import subprocess
import sys

import numpy
import pytest

import facefusion.choices
from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager, video_manager
from facefusion.common_helper import get_first, get_last
from facefusion.download import conditional_download
from facefusion.filesystem import resolve_file_paths
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from facefusion.types import VisionFrame, WorkflowStrategy
from facefusion.vision import read_image, read_video_frame
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_path, is_test_output_file, is_test_output_sequence, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	process_manager.start()

	video_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
		)
	)

	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '--face-mask-types', 'box', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_example_file('target-240p-deep-swapper.png') ]
	subprocess.run(commands)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def count_swap_pixel_total(target_vision_frame : VisionFrame, output_vision_frame : VisionFrame) -> int:
	difference_frame = numpy.abs(target_vision_frame.astype(numpy.int16) - output_vision_frame.astype(numpy.int16)).max(axis = 2)
	return int(numpy.count_nonzero(difference_frame > 30))


def test_pre_process() -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '-t', 'invalid', '-o', get_test_output_path('test-pre-process.jpg') ]
	run_process = subprocess.run(commands, capture_output = True)

	assert get_last(run_process.stderr.decode().splitlines()) == '[FACEFUSION.CORE] choose an image or video for the target!'
	assert is_test_output_file('test-pre-process.jpg') is False
	assert run_process.returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('invalid/test-pre-process.jpg') ]
	run_process = subprocess.run(commands, capture_output = True)

	assert get_last(run_process.stderr.decode().splitlines()) == '[FACEFUSION.CORE] specify the output image or video within a directory!'
	assert is_test_output_file('invalid/test-pre-process.jpg') is False
	assert run_process.returncode == 1


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_swap_face_to_image(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('test-swap-face-to-image.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-swap-face-to-image.jpg') is True
	assert count_swap_pixel_total(read_image(get_test_example_file('target-240p.jpg')), read_image(get_test_output_path('test-swap-face-to-image.jpg'))) > 500


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_swap_face_to_video(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-swap-face-to-video.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-swap-face-to-video.mp4') is True
	assert count_swap_pixel_total(read_video_frame(get_test_example_file('target-240p.mp4')), read_video_frame(get_test_output_path('test-swap-face-to-video.mp4'))) > 500


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_swap_face_to_video_as_frames(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video:frames', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-swap-face-to-video-as-frames'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_sequence(get_test_output_path('test-swap-face-to-video-as-frames')) is True
	assert count_swap_pixel_total(read_video_frame(get_test_example_file('target-240p.mp4')), read_image(get_first(resolve_file_paths(get_test_output_path('test-swap-face-to-video-as-frames'))))) > 500


@pytest.mark.parametrize('face_mask_type, mask_pixel_total',
[
	('occlusion', 10),
	('area', 500),
	('region', 500)
])
def test_swap_face(face_mask_type : str, mask_pixel_total : int) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'deep_swapper', '--face-mask-types', 'box', face_mask_type, '--face-mask-areas', 'mouth', '--face-mask-regions', 'nose', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('test-swap-face.png') ]

	assert subprocess.run(commands).returncode == 0
	assert count_swap_pixel_total(read_image(get_test_example_file('target-240p-deep-swapper.png')), read_image(get_test_output_path('test-swap-face.png'))) > mask_pixel_total
