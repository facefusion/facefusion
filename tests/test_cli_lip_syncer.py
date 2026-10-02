import subprocess
import sys

import numpy
import pytest

import facefusion.choices
from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager, video_manager
from facefusion.common_helper import get_first
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
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
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


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def count_sync_pixel_total(target_vision_frame : VisionFrame, output_vision_frame : VisionFrame) -> int:
	difference_frame = numpy.abs(target_vision_frame.astype(numpy.int16) - output_vision_frame.astype(numpy.int16)).max(axis = 2)
	return int(numpy.count_nonzero(difference_frame > 30))


def test_pre_process_without_source_audio() -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video', '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-pre-process-without-source-audio.mp4'), '--trim-frame-end', '1' ]
	completed_process = subprocess.run(commands, capture_output = True)

	assert 'choose an audio for the source' in completed_process.stderr.decode()
	assert completed_process.returncode == 1
	assert is_test_output_file('test-pre-process-without-source-audio.mp4') is False


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_sync_lip_to_image(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'audio-to-image:video', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('test_sync_lip_to_image.mp4') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test_sync_lip_to_image.mp4') is True
	assert count_sync_pixel_total(read_image(get_test_example_file('target-240p.jpg')), read_video_frame(get_test_output_path('test_sync_lip_to_image.mp4'))) > 50


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_sync_lip_to_image_as_frames(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'audio-to-image:frames', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('test_sync_lip_to_image_as_frames') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_sequence(get_test_output_path('test_sync_lip_to_image_as_frames')) is True
	assert count_sync_pixel_total(read_image(get_test_example_file('target-240p.jpg')), read_image(get_first(resolve_file_paths(get_test_output_path('test_sync_lip_to_image_as_frames'))))) > 50


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_sync_lip_to_video(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test_sync_lip_to_video.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test_sync_lip_to_video.mp4') is True
	assert count_sync_pixel_total(read_video_frame(get_test_example_file('target-240p.mp4')), read_video_frame(get_test_output_path('test_sync_lip_to_video.mp4'))) > 50


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_sync_lip_to_video_as_frames(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video:frames', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test_sync_lip_to_video_as_frames'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_sequence(get_test_output_path('test_sync_lip_to_video_as_frames')) is True
	assert count_sync_pixel_total(read_video_frame(get_test_example_file('target-240p.mp4')), read_image(get_first(resolve_file_paths(get_test_output_path('test_sync_lip_to_video_as_frames'))))) > 50


def test_sync_lip_with_edtalk() -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video', '--jobs-path', get_test_jobs_directory(), '--processors', 'lip_syncer', '--lip-syncer-model', 'edtalk_256', '--face-mask-types', 'box', 'occlusion', '-s', get_test_example_file('source.mp3'), '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-sync-lip-with-edtalk.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-sync-lip-with-edtalk.mp4') is True
	assert count_sync_pixel_total(read_video_frame(get_test_example_file('target-240p.mp4')), read_video_frame(get_test_output_path('test-sync-lip-with-edtalk.mp4'))) > 300
