import subprocess
import pytest

from facefusion.download import conditional_download
from facefusion.vision import detect_image_resolution, restrict_image_resolution, create_image_resolutions, get_video_frame, count_video_frame_total, detect_video_fps, restrict_video_fps, detect_video_resolution, restrict_video_resolution, create_video_resolutions, normalize_resolution, pack_resolution, unpack_resolution


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '.assets/examples/target-240p.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vframes', '1', '.assets/examples/target-1080p.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vframes', '1', '-vf', 'transpose=0', '.assets/examples/target-240p-90deg.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vframes', '1', '-vf', 'transpose=0', '.assets/examples/target-1080p-90deg.jpg' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=25', '.assets/examples/target-240p-25fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=30', '.assets/examples/target-240p-30fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=60', '.assets/examples/target-240p-60fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'transpose=0', '.assets/examples/target-240p-90deg.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vf', 'transpose=0', '.assets/examples/target-1080p-90deg.mp4' ])


def test_detect_image_resolution() -> None:
	assert detect_image_resolution('.assets/examples/target-240p.jpg') == (426, 226)
	assert detect_image_resolution('.assets/examples/target-240p-90deg.jpg') == (226, 426)
	assert detect_image_resolution('.assets/examples/target-1080p.jpg') == (2048, 1080)
	assert detect_image_resolution('.assets/examples/target-1080p-90deg.jpg') == (1080, 2048)
	assert detect_image_resolution('invalid') is None


def test_restrict_image_resolution() -> None:
	assert restrict_image_resolution('.assets/examples/target-1080p.jpg', (426, 226)) == (426, 226)
	assert restrict_image_resolution('.assets/examples/target-1080p.jpg', (2048, 1080)) == (2048, 1080)
	assert restrict_image_resolution('.assets/examples/target-1080p.jpg', (4096, 2160)) == (2048, 1080)


def test_create_image_resolutions() -> None:
	assert create_image_resolutions((426, 226)) == [ '106x56', '212x112', '320x170', '426x226', '640x340', '852x452', '1064x564', '1278x678', '1492x792', '1704x904' ]
	assert create_image_resolutions((226, 426)) == [ '56x106', '112x212', '170x320', '226x426', '340x640', '452x852', '564x1064', '678x1278', '792x1492', '904x1704' ]
	assert create_image_resolutions((2048, 1080)) == [ '512x270', '1024x540', '1536x810', '2048x1080', '3072x1620', '4096x2160', '5120x2700', '6144x3240', '7168x3780', '8192x4320' ]
	assert create_image_resolutions((1080, 2048)) == [ '270x512', '540x1024', '810x1536', '1080x2048', '1620x3072', '2160x4096', '2700x5120', '3240x6144', '3780x7168', '4320x8192' ]
	assert create_image_resolutions(None) == []


def test_get_video_frame() -> None:
	assert get_video_frame('.assets/examples/target-240p-25fps.mp4') is not None
	assert get_video_frame('invalid') is None


def test_count_video_frame_total() -> None:
	assert count_video_frame_total('.assets/examples/target-240p-25fps.mp4') == 270
	assert count_video_frame_total('.assets/examples/target-240p-30fps.mp4') == 324
	assert count_video_frame_total('.assets/examples/target-240p-60fps.mp4') == 648
	assert count_video_frame_total('invalid') == 0


def test_detect_video_fps() -> None:
	assert detect_video_fps('.assets/examples/target-240p-25fps.mp4') == 25.0
	assert detect_video_fps('.assets/examples/target-240p-30fps.mp4') == 30.0
	assert detect_video_fps('.assets/examples/target-240p-60fps.mp4') == 60.0
	assert detect_video_fps('invalid') is None


def test_restrict_video_fps() -> None:
	assert restrict_video_fps('.assets/examples/target-1080p.mp4', 20.0) == 20.0
	assert restrict_video_fps('.assets/examples/target-1080p.mp4', 25.0) == 25.0
	assert restrict_video_fps('.assets/examples/target-1080p.mp4', 60.0) == 25.0


def test_detect_video_resolution() -> None:
	assert detect_video_resolution('.assets/examples/target-240p.mp4') == (426, 226)
	assert detect_video_resolution('.assets/examples/target-240p-90deg.mp4') == (226, 426)
	assert detect_video_resolution('.assets/examples/target-1080p.mp4') == (2048, 1080)
	assert detect_video_resolution('.assets/examples/target-1080p-90deg.mp4') == (1080, 2048)
	assert detect_video_resolution('invalid') is None


def test_restrict_video_resolution() -> None:
	assert restrict_video_resolution('.assets/examples/target-1080p.mp4', (426, 226)) == (426, 226)
	assert restrict_video_resolution('.assets/examples/target-1080p.mp4', (2048, 1080)) == (2048, 1080)
	assert restrict_video_resolution('.assets/examples/target-1080p.mp4', (4096, 2160)) == (2048, 1080)


def test_create_video_resolutions() -> None:
	assert create_video_resolutions((426, 226)) == [ '426x226', '452x240', '678x360', '904x480', '1018x540', '1358x720', '2036x1080', '2714x1440', '4072x2160', '8144x4320' ]
	assert create_video_resolutions((226, 426)) == [ '226x426', '240x452', '360x678', '480x904', '540x1018', '720x1358', '1080x2036', '1440x2714', '2160x4072', '4320x8144' ]
	assert create_video_resolutions((2048, 1080)) == [ '456x240', '682x360', '910x480', '1024x540', '1366x720', '2048x1080', '2730x1440', '4096x2160', '8192x4320' ]
	assert create_video_resolutions((1080, 2048)) == [ '240x456', '360x682', '480x910', '540x1024', '720x1366', '1080x2048', '1440x2730', '2160x4096', '4320x8192' ]
	assert create_video_resolutions(None) == []


def test_normalize_resolution() -> None:
	assert normalize_resolution((2.5, 2.5)) == (2, 2)
	assert normalize_resolution((3.0, 3.0)) == (4, 4)
	assert normalize_resolution((6.5, 6.5)) == (6, 6)


def test_pack_resolution() -> None:
	assert pack_resolution((1, 1)) == '0x0'
	assert pack_resolution((2, 2)) == '2x2'


def test_unpack_resolution() -> None:
	assert unpack_resolution('0x0') == (0, 0)
	assert unpack_resolution('2x2') == (2, 2)
