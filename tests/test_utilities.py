import subprocess
import pytest

from facefusion.utilities import conditional_download, detect_fps


@pytest.fixture(scope = 'module', autouse = True)
def setup() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vf', 'fps=25', '.assets/examples/target-1080p-25fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vf', 'fps=30', '.assets/examples/target-1080p-30fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vf', 'fps=60', '.assets/examples/target-1080p-60fps.mp4' ])


def test_detect_fps() -> None:
	assert detect_fps('.assets/examples/target-1080p-25fps.mp4') == 25.0
	assert detect_fps('.assets/examples/target-1080p-30fps.mp4') == 30.0
	assert detect_fps('.assets/examples/target-1080p-60fps.mp4') == 60.0
