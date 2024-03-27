import subprocess
import sys
import pytest
from pathlib import Path

from facefusion.download import conditional_download


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	Path('.assets/examples_multiple/output').mkdir(parents = True, exist_ok = True)
	Path('.assets/examples_multiple/target/img').mkdir(parents = True, exist_ok = True)
	Path('.assets/examples_multiple/target/video').mkdir(parents = True, exist_ok = True)
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	conditional_download('.assets/examples_multiple/source',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg'
	])
	conditional_download('.assets/examples_multiple/target/video',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples/target-240p.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples_multiple/target/img/target-1-240p.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples_multiple/target/img/target-2-240p.jpg' ])


def test_debug_face_to_image() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_debugger', '-t', '.assets/examples/target-240p.jpg', '-o', '.assets/examples/test_debug_face_to_image.jpg', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()


def test_debug_face_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_debugger', '-t', '.assets/examples/target-240p.mp4', '-o', '.assets/examples/test_debug_face_to_video.mp4', '--trim-frame-end', '10', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()


def test_enhance_face_to_image() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_enhancer', '-t', '.assets/examples/target-240p.jpg', '-o', '.assets/examples/test_enhance_face_to_image.jpg', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()

def test_loop_enhance_faces_to_images() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_enhancer', '-td', '.assets/examples_multiple/target/img', '-o', '.assets/examples_multiple/output', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()

def test_enhance_face_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_enhancer', '-t', '.assets/examples/target-240p.mp4', '-o', '.assets/examples/test_enhance_face_to_video.mp4', '--trim-frame-end', '10', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()

def test_loop_enhance_face_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_enhancer', '-td', '.assets/examples_multiple/target/video', '-o', '.assets/examples_multiple/output/test_enhance_face_to_video.mp4', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()

def test_loop_swap_faces_to_images() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_swapper', '-sd', '.assets/examples_multiple/source', '-td', '.assets/examples_multiple/target/img', '-o', '.assets/examples_multiple/output', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()

def test_swap_face_to_image() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_swapper', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-240p.jpg', '-o', '.assets/examples/test_swap_face_to_image.jpg', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()

def test_swap_face_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_swapper', '-s', '.assets/examples/source.jpg', '-t', '.assets/examples/target-240p.mp4', '-o', '.assets/examples/test_swap_face_to_video.mp4', '--trim-frame-end', '10', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()

def test_loop_swap_face_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'face_swapper', '-sd', '.assets/examples_multiple/source', '-td', '.assets/examples_multiple/target/video', '-o', '.assets/examples_multiple/output/test_swap_face_to_video.mp4', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()

def test_sync_lip_to_image() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'lip_syncer', '-s', '.assets/examples/source.mp3', '-t', '.assets/examples/target-240p.jpg', '-o', '.assets/examples/test_sync_lip_to_image.jpg', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'image succeed' in run.stdout.decode()

def test_sync_lip_to_video() -> None:
	commands = [ sys.executable, 'run.py', '--frame-processors', 'lip_syncer', '-s', '.assets/examples/source.mp3', '-t', '.assets/examples/target-240p.mp4', '-o', '.assets/examples/test_sync_lip_to_video.mp4', '--trim-frame-end', '10', '--headless' ]
	run = subprocess.run(commands, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

	assert run.returncode == 0
	assert 'video succeed' in run.stdout.decode()
