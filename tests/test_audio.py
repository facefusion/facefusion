import subprocess
import pytest

#from facefusion.audio import get_audio_frame
from facefusion.download import conditional_download


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.mp3'
	])
	subprocess.run(['ffmpeg', '-i', '.assets/examples/source.mp3', '.assets/examples/source.wav'])


def test_get_audio_frame() -> None:
	pass
	# todo: testing
	#assert get_audio_frame('.assets/examples/source.mp3', 25) is not None
	# assert get_audio_frame('.assets/examples/source.wav', 25) is not None
	#assert get_audio_frame('invalid', 25) is None
