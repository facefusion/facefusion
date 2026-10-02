import subprocess
import sys
from typing import List, Tuple

import numpy
import pytest

import facefusion.choices
from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.common_helper import get_first, get_last
from facefusion.download import conditional_download
from facefusion.filesystem import resolve_file_paths
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from facefusion.types import VisionFrame, WorkflowStrategy
from facefusion.vision import read_image
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_path, is_test_output_file, is_test_output_sequence, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
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

	for target_angle, target_filter in [ ('90', 'transpose=0'), ('180', 'hflip,vflip'), ('270', 'transpose=3') ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				[
					'-vframes',
					'1'
				],
				[
					'-vf',
					target_filter
				],
				ffmpeg_builder.set_output(get_test_example_file('target-240p-' + target_angle + 'deg.jpg'))
			)
		)

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'5'
			],
			[
				'-vf',
				'drawbox=enable=\'eq(n,2)\':color=black:t=fill'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p-gap.mp4'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


def count_color_pixel_total(vision_frame : VisionFrame, color : Tuple[int, int, int]) -> int:
	return int(numpy.count_nonzero(numpy.all(vision_frame == color, axis = 2)))


def run_debug_face_to_frame(face_debugger_items : List[str], trim_frame_start : int, face_aligner_score : str, face_mask_type : str, output_name : str) -> int:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video:frames', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '--face-debugger-items' ] + face_debugger_items + [ '--face-aligner-score', face_aligner_score, '--face-mask-types', face_mask_type, '--face-tracker-score', '0.3', '-t', get_test_example_file('target-240p-gap.mp4'), '-o', get_test_output_path(output_name), '--trim-frame-start', str(trim_frame_start), '--trim-frame-end', str(trim_frame_start + 1) ]

	return subprocess.run(commands).returncode


def read_test_output_frame(output_name : str) -> VisionFrame:
	return read_image(get_first(resolve_file_paths(get_test_output_path(output_name))))


def test_pre_process() -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', 'invalid', '-o', get_test_output_path('test-pre-process.jpg') ]
	run_process = subprocess.run(commands, capture_output = True)

	assert get_last(run_process.stderr.decode().splitlines()) == '[FACEFUSION.CORE] choose an image or video for the target!'
	assert is_test_output_file('test-pre-process.jpg') is False
	assert run_process.returncode == 1

	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('invalid/test-pre-process.jpg') ]
	run_process = subprocess.run(commands, capture_output = True)

	assert get_last(run_process.stderr.decode().splitlines()) == '[FACEFUSION.CORE] specify the output image or video within a directory!'
	assert is_test_output_file('invalid/test-pre-process.jpg') is False
	assert run_process.returncode == 1


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_debug_face_to_image(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.jpg'), '-o', get_test_output_path('test-debug-face-to-image.jpg') ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-debug-face-to-image.jpg') is True


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_debug_face_to_video(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-debug-face-to-video.mp4'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file('test-debug-face-to-video.mp4') is True


@pytest.mark.parametrize('workflow_strategy', facefusion.choices.workflow_strategies)
def test_debug_face_to_video_as_frames(workflow_strategy : WorkflowStrategy) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-video:frames', '--workflow-strategy', workflow_strategy, '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '-t', get_test_example_file('target-240p.mp4'), '-o', get_test_output_path('test-debug-face-to-video-as-frames'), '--trim-frame-end', '1' ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_sequence(get_test_output_path('test-debug-face-to-video-as-frames')) is True


@pytest.mark.parametrize('target_name', [ 'target-240p.jpg', 'target-240p-90deg.jpg', 'target-240p-180deg.jpg', 'target-240p-270deg.jpg' ])
def test_draw_bounding_box(target_name : str) -> None:
	commands = [ sys.executable, 'facefusion.py', 'run', '--workflow-mode', 'image-to-image', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_debugger', '--face-debugger-items', 'bounding-box', '--face-detector-angles', '0', '90', '180', '270', '-t', get_test_example_file(target_name), '-o', get_test_output_path('test-draw-bounding-box.png') ]

	assert subprocess.run(commands).returncode == 0
	assert count_color_pixel_total(read_image(get_test_output_path('test-draw-bounding-box.png')), (0, 0, 255)) > 300
	assert count_color_pixel_total(read_image(get_test_output_path('test-draw-bounding-box.png')), (100, 100, 255)) > 150


@pytest.mark.parametrize('face_mask_type, trim_frame_start, face_aligner_score, mask_color',
[
	('box', 1, '0.5', (0, 255, 0)),
	('occlusion', 1, '0.5', (0, 255, 0)),
	('area', 1, '0.5', (0, 255, 0)),
	('region', 1, '0.5', (0, 255, 0)),
	('box', 1, '0.0', (255, 255, 0)),
	('box', 2, '0.5', (0, 165, 255))
])
def test_draw_face_mask(face_mask_type : str, trim_frame_start : int, face_aligner_score : str, mask_color : Tuple[int, int, int]) -> None:
	assert run_debug_face_to_frame([ 'face-mask' ], trim_frame_start, face_aligner_score, face_mask_type, 'test-draw-face-mask') == 0
	assert count_color_pixel_total(read_test_output_frame('test-draw-face-mask'), mask_color) > 300


@pytest.mark.parametrize('trim_frame_start, point_color',
[
	(1, (0, 0, 255)),
	(2, (0, 165, 255))
])
def test_draw_face_landmark_5(trim_frame_start : int, point_color : Tuple[int, int, int]) -> None:
	assert run_debug_face_to_frame([ 'face-landmark-5' ], trim_frame_start, '0.5', 'box', 'test-draw-face-landmark-5') == 0
	assert count_color_pixel_total(read_test_output_frame('test-draw-face-landmark-5'), point_color) > 20


@pytest.mark.parametrize('trim_frame_start, face_aligner_score, point_color',
[
	(1, '0.5', (0, 255, 0)),
	(1, '0.0', (255, 255, 0)),
	(2, '0.5', (0, 165, 255))
])
def test_draw_face_landmark_5_68(trim_frame_start : int, face_aligner_score : str, point_color : Tuple[int, int, int]) -> None:
	assert run_debug_face_to_frame([ 'face-landmark-5/68' ], trim_frame_start, face_aligner_score, 'box', 'test-draw-face-landmark-5-68') == 0
	assert count_color_pixel_total(read_test_output_frame('test-draw-face-landmark-5-68'), point_color) > 20


@pytest.mark.parametrize('trim_frame_start, face_aligner_score, point_color',
[
	(1, '0.5', (0, 255, 0)),
	(1, '0.0', (255, 255, 0)),
	(2, '0.5', (0, 165, 255))
])
def test_draw_face_landmark_68(trim_frame_start : int, face_aligner_score : str, point_color : Tuple[int, int, int]) -> None:
	assert run_debug_face_to_frame([ 'face-landmark-68' ], trim_frame_start, face_aligner_score, 'box', 'test-draw-face-landmark-68') == 0
	assert count_color_pixel_total(read_test_output_frame('test-draw-face-landmark-68'), point_color) > 300


@pytest.mark.parametrize('trim_frame_start, point_color',
[
	(1, (255, 255, 0)),
	(2, (0, 165, 255))
])
def test_draw_face_landmark_68_5(trim_frame_start : int, point_color : Tuple[int, int, int]) -> None:
	assert run_debug_face_to_frame([ 'face-landmark-68/5' ], trim_frame_start, '0.5', 'box', 'test-draw-face-landmark-68-5') == 0
	assert count_color_pixel_total(read_test_output_frame('test-draw-face-landmark-68-5'), point_color) > 300
