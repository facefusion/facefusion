
from unittest.mock import patch

import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager, video_manager
from facefusion.common_helper import get_first
from facefusion.download import conditional_download
from facefusion.vision import blend_frame, blend_vision_frames, calculate_histogram_difference, conditional_match_frame_color, conditional_merge_vision_mask, count_video_frame_total, create_empty_vision_frame, create_tile_frames, detect_frame_orientation, detect_image_resolution, detect_video_duration, detect_video_fps, detect_video_resolution, extract_vision_mask, fit_contain_frame, fit_cover_frame, from_buffer, is_vision_frame, is_vision_frames, match_frame_color, merge_tile_frames, merge_vision_mask, normalize_resolution, obscure_frame, pack_resolution, predict_video_frame_total, read_image, read_video_frame, resolve_extract_frame_index, resolve_target_frame_index, restrict_frame, restrict_image_resolution, restrict_trim_video_frame, restrict_video_fps, restrict_video_resolution, scale_resolution, select_video_frames, to_buffer, to_strip_buffer, unpack_resolution, write_image
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_output_path, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	process_manager.start()

	video_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-1080p.mp4'
	])

	for target_name in [ 'target-240p', 'target-1080p' ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file(target_name + '.mp4')),
				[
					'-vframes',
					'1'
				],
				ffmpeg_builder.set_output(get_test_example_file(target_name + '.jpg'))
			)
		)

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('目标-240p.webp'))
		)
	)

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			[
				'-vf',
				'hue=s=0'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p-0sat.jpg'))
		)
	)

	for target_name in [ 'target-240p', 'target-1080p' ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file(target_name + '.mp4')),
				[
					'-vframes',
					'1'
				],
				[
					'-vf',
					'transpose=0'
				],
				ffmpeg_builder.set_output(get_test_example_file(target_name + '-90deg.jpg'))
			)
		)

	for video_fps in [ 25, 30, 60 ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.set_video_fps(video_fps),
				ffmpeg_builder.set_output(get_test_example_file('target-240p-' + str(video_fps) + 'fps.mp4'))
			)
		)

	for target_name in [ 'target-240p', 'target-1080p' ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file(target_name + '.mp4')),
				[
					'-vf',
					'transpose=0'
				],
				ffmpeg_builder.set_output(get_test_example_file(target_name + '-90deg.mp4'))
			)
		)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_read_image() -> None:
	assert read_image(get_test_example_file('target-240p.jpg')).shape == (226, 426, 3)
	assert read_image(get_test_example_file('目标-240p.webp')).shape == (226, 426, 3)
	assert read_image('invalid') is None

	with patch('facefusion.vision.is_windows', return_value = True):
		assert read_image(get_test_example_file('目标-240p.webp')).shape == (226, 426, 3)


def test_write_image() -> None:
	vision_frame = read_image(get_test_example_file('target-240p.jpg'))

	assert write_image(get_test_output_path('target-240p.jpg'), vision_frame) is True
	assert write_image(get_test_output_path('目标-240p.webp'), vision_frame) is True
	assert write_image('', vision_frame) is False

	with patch('facefusion.vision.is_windows', return_value = True):
		assert write_image(get_test_output_path('目标-240p-windows.webp'), vision_frame) is True

	assert read_image(get_test_output_path('目标-240p-windows.webp')).shape == (226, 426, 3)


def test_detect_image_resolution() -> None:
	assert detect_image_resolution(get_test_example_file('target-240p.jpg')) == (426, 226)
	assert detect_image_resolution(get_test_example_file('target-240p-90deg.jpg')) == (226, 426)
	assert detect_image_resolution(get_test_example_file('target-1080p.jpg')) == (2048, 1080)
	assert detect_image_resolution(get_test_example_file('target-1080p-90deg.jpg')) == (1080, 2048)
	assert detect_image_resolution('invalid') is None


def test_restrict_image_resolution() -> None:
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (426, 226)) == (426, 226)
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (2048, 1080)) == (2048, 1080)
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (4096, 2160)) == (2048, 1080)


def test_read_video_frame() -> None:
	target_path = get_test_example_file('target-240p-25fps.mp4')

	assert read_video_frame(target_path).shape == (226, 426, 3)
	assert numpy.array_equal(read_video_frame(target_path, 49), select_video_frames(target_path, 49, 5)[5])
	assert numpy.array_equal(read_video_frame(target_path, 50), select_video_frames(target_path, 50, 5)[5])
	assert numpy.array_equal(read_video_frame(target_path, 51), select_video_frames(target_path, 51, 5)[5])
	assert read_video_frame('invalid') is None


def test_select_video_frames() -> None:
	assert len(select_video_frames(get_test_example_file('target-240p-25fps.mp4'), 50, 5)) == 11
	assert len(select_video_frames(get_test_example_file('target-240p-25fps.mp4'), 1, 5)) == 11
	assert len(select_video_frames(get_test_example_file('target-240p-25fps.mp4'), 269, 5)) == 11
	assert select_video_frames('invalid', 50, 5) == []


def test_count_video_frame_total() -> None:
	assert count_video_frame_total(get_test_example_file('target-240p-25fps.mp4')) == 270
	assert count_video_frame_total(get_test_example_file('target-240p-30fps.mp4')) == 324
	assert count_video_frame_total(get_test_example_file('target-240p-60fps.mp4')) == 648
	assert count_video_frame_total('invalid') == 0


def test_predict_video_frame_total() -> None:
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 12.5, 0, 100) == 50
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 25, 0, 100) == 100
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 25, 0, 200) == 200
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 6.25, 0, 270) == 68
	assert predict_video_frame_total(get_test_example_file('target-240p-30fps.mp4'), 9.49, 40, 200) == 50
	assert predict_video_frame_total('invalid', 25, 0, 100) == 0


def test_resolve_extract_frame_index() -> None:
	assert resolve_extract_frame_index(25, 12.5, 100) == 50
	assert resolve_extract_frame_index(25, 25, 100) == 100
	assert resolve_extract_frame_index(25, 6.25, 270) == 68
	assert resolve_extract_frame_index(30, 9.49, 40) == 13


def test_resolve_target_frame_index() -> None:
	assert resolve_target_frame_index(25, 12.5, 50) == 100
	assert resolve_target_frame_index(25, 25, 100) == 100
	assert resolve_target_frame_index(25, 6.25, 1) == 5
	assert resolve_target_frame_index(30, 9.49, 13) == 42


def test_detect_video_fps() -> None:
	assert detect_video_fps(get_test_example_file('target-240p-25fps.mp4')) == 25.0
	assert detect_video_fps(get_test_example_file('target-240p-30fps.mp4')) == 30.0
	assert detect_video_fps(get_test_example_file('target-240p-60fps.mp4')) == 60.0
	assert detect_video_fps('invalid') is None


def test_restrict_video_fps() -> None:
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 20.0) == 20.0
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 25.0) == 25.0
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 60.0) == 25.0


def test_detect_video_duration() -> None:
	assert detect_video_duration(get_test_example_file('target-240p.mp4')) == 10.8
	assert detect_video_duration('invalid') == 0


def test_restrict_trim_frame() -> None:
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), 0, 200) == (0, 200)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), 70, 270) == (70, 270)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), -10, None) == (0, 270)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), None, -10) == (0, 0)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), 280, None) == (270, 270)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), None, 280) == (0, 270)
	assert restrict_trim_video_frame(get_test_example_file('target-240p.mp4'), None, None) == (0, 270)


def test_detect_video_resolution() -> None:
	assert detect_video_resolution(get_test_example_file('target-240p.mp4')) == (426, 226)
	assert detect_video_resolution(get_test_example_file('target-240p-90deg.mp4')) == (226, 426)
	assert detect_video_resolution(get_test_example_file('target-1080p.mp4')) == (2048, 1080)
	assert detect_video_resolution(get_test_example_file('target-1080p-90deg.mp4')) == (1080, 2048)
	assert detect_video_resolution('invalid') is None


def test_restrict_video_resolution() -> None:
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (426, 226)) == (426, 226)
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (2048, 1080)) == (2048, 1080)
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (4096, 2160)) == (2048, 1080)


def test_scale_resolution() -> None:
	assert scale_resolution((426, 226), 0.5) == (212, 112)
	assert scale_resolution((2048, 1080), 1.0) == (2048, 1080)
	assert scale_resolution((4096, 2160), 2.0) == (8192, 4320)


def test_normalize_resolution() -> None:
	assert normalize_resolution((2.5, 2.5)) == (2, 2)
	assert normalize_resolution((3.0, 3.0)) == (4, 4)
	assert normalize_resolution((6.5, 6.5)) == (6, 6)
	assert normalize_resolution((0, 0)) == (0, 0)
	assert normalize_resolution((-2, 2)) == (0, 0)


def test_pack_resolution() -> None:
	assert pack_resolution((1, 1)) == '0x0'
	assert pack_resolution((2, 2)) == '2x2'


def test_unpack_resolution() -> None:
	assert unpack_resolution('0x0') == (0, 0)
	assert unpack_resolution('2x2') == (2, 2)
	assert unpack_resolution('invalid') == (0, 0)


def test_detect_frame_orientation() -> None:
	assert detect_frame_orientation(numpy.zeros((100, 200, 3))) == 'landscape'
	assert detect_frame_orientation(numpy.zeros((200, 100, 3))) == 'portrait'
	assert detect_frame_orientation(numpy.zeros((100, 100, 3))) == 'portrait'


def test_is_vision_frame() -> None:
	assert is_vision_frame(numpy.zeros((2, 2, 3))) is True
	assert is_vision_frame(numpy.zeros((2, 2))) is False
	assert is_vision_frame(None) is False


def test_is_vision_frames() -> None:
	assert is_vision_frames([ numpy.zeros((2, 2, 3)), numpy.zeros((2, 2, 3)) ]) is True
	assert is_vision_frames([ numpy.zeros((2, 2, 3)), numpy.zeros((2, 2)) ]) is False
	assert is_vision_frames([]) is False


def test_restrict_frame() -> None:
	vision_frame = numpy.zeros((100, 200, 3), numpy.uint8)

	assert restrict_frame(vision_frame, (100, 100)).shape == (50, 100, 3)
	assert restrict_frame(vision_frame, (200, 25)).shape == (25, 50, 3)
	assert restrict_frame(vision_frame, (200, 100)) is vision_frame
	assert restrict_frame(vision_frame, (400, 400)) is vision_frame


def test_fit_contain_frame() -> None:
	vision_frame = numpy.full((100, 200, 3), 255, numpy.uint8)
	contain_vision_frame = fit_contain_frame(vision_frame, (100, 100))

	assert contain_vision_frame.shape == (100, 100, 3)
	assert contain_vision_frame[24, 50].tolist() == [ 0, 0, 0 ]
	assert contain_vision_frame[25, 50].tolist() == [ 255, 255, 255 ]
	assert contain_vision_frame[74, 50].tolist() == [ 255, 255, 255 ]
	assert contain_vision_frame[75, 50].tolist() == [ 0, 0, 0 ]

	contain_vision_frame = fit_contain_frame(vision_frame, (300, 300))

	assert contain_vision_frame.shape == (300, 300, 3)
	assert contain_vision_frame[74, 0].tolist() == [ 0, 0, 0 ]
	assert contain_vision_frame[75, 0].tolist() == [ 255, 255, 255 ]
	assert fit_contain_frame(numpy.zeros((101, 200, 3), numpy.uint8), (101, 100)).shape == (100, 101, 3)

	contain_vision_frame = fit_contain_frame(numpy.full((200, 100, 3), 255, numpy.uint8), (100, 100))

	assert contain_vision_frame[50, 24].tolist() == [ 0, 0, 0 ]
	assert contain_vision_frame[50, 25].tolist() == [ 255, 255, 255 ]
	assert contain_vision_frame[50, 74].tolist() == [ 255, 255, 255 ]
	assert contain_vision_frame[50, 75].tolist() == [ 0, 0, 0 ]


def test_fit_cover_frame() -> None:
	vision_frame = numpy.zeros((100, 200, 3), numpy.uint8)
	vision_frame[:, :, 0] = numpy.arange(200)

	cover_vision_frame = fit_cover_frame(vision_frame, (100, 100))

	assert cover_vision_frame.shape == (100, 100, 3)
	assert cover_vision_frame[0, 0, 0] == 50
	assert cover_vision_frame[0, -1, 0] == 149

	cover_vision_frame = fit_cover_frame(vision_frame, (400, 100))

	assert cover_vision_frame.shape == (100, 400, 3)
	assert cover_vision_frame[0, 0, 0] == 0
	assert cover_vision_frame[0, -1, 0] == 199
	assert fit_cover_frame(vision_frame, (200, 200)).shape == (200, 200, 3)


def test_obscure_frame() -> None:
	vision_frame = numpy.zeros((100, 100, 3), numpy.uint8)
	vision_frame[:, 50:] = 255
	obscure_vision_frame = obscure_frame(vision_frame)

	assert obscure_vision_frame.shape == (100, 100, 3)
	assert obscure_vision_frame[50, 0].tolist() == [ 0, 0, 0 ]
	assert obscure_vision_frame[50, 49].tolist() == [ 125, 125, 125 ]
	assert obscure_vision_frame[50, 50].tolist() == [ 130, 130, 130 ]
	assert obscure_vision_frame[50, 99].tolist() == [ 255, 255, 255 ]


def test_blend_frame() -> None:
	source_vision_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	target_vision_frame = numpy.full((2, 2, 3), 200, numpy.uint8)

	assert blend_frame(source_vision_frame, target_vision_frame, 0.0)[0, 0].tolist() == [ 0, 0, 0 ]
	assert blend_frame(source_vision_frame, target_vision_frame, 0.25)[0, 0].tolist() == [ 50, 50, 50 ]
	assert blend_frame(source_vision_frame, target_vision_frame, 1.0)[0, 0].tolist() == [ 200, 200, 200 ]


def test_calc_histogram_difference() -> None:
	source_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	target_vision_frame = read_image(get_test_example_file('target-240p-0sat.jpg'))

	assert calculate_histogram_difference(source_vision_frame, source_vision_frame) == 1.0
	assert calculate_histogram_difference(source_vision_frame, target_vision_frame) < 0.5


def test_conditional_match_frame_color() -> None:
	source_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	target_vision_frame = read_image(get_test_example_file('target-240p-0sat.jpg'))
	output_vision_frame = conditional_match_frame_color(source_vision_frame, target_vision_frame)

	assert calculate_histogram_difference(source_vision_frame, output_vision_frame) > calculate_histogram_difference(source_vision_frame, target_vision_frame)
	assert numpy.array_equal(conditional_match_frame_color(source_vision_frame, source_vision_frame.copy()), source_vision_frame) is True


def test_match_frame_color() -> None:
	source_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	target_vision_frame = read_image(get_test_example_file('target-240p-0sat.jpg'))
	output_vision_frame = match_frame_color(source_vision_frame, target_vision_frame)

	assert calculate_histogram_difference(source_vision_frame, output_vision_frame) > 0.5


def test_blend_vision_frames() -> None:
	source_vision_frame = numpy.zeros((2, 2, 3), numpy.uint8)
	target_vision_frame = numpy.full((2, 2, 3), 200, numpy.uint8)

	assert blend_vision_frames(source_vision_frame, target_vision_frame, 0.75)[0, 0].tolist() == [ 150, 150, 150 ]


def test_create_empty_vision_frame() -> None:
	assert create_empty_vision_frame().shape == (1, 1, 3)
	assert create_empty_vision_frame().dtype == numpy.uint8
	assert create_empty_vision_frame().sum() == 0


def test_from_buffer() -> None:
	vision_frame = numpy.full((100, 200, 3), 255, numpy.uint8)

	assert from_buffer(to_buffer(vision_frame)).shape == (100, 200, 3)
	assert from_buffer(bytes()) is None


def test_to_buffer() -> None:
	vision_buffer = to_buffer(numpy.full((100, 200, 3), 255, numpy.uint8))

	assert vision_buffer[:3] == bytes([ 255, 216, 255 ])
	assert from_buffer(vision_buffer)[50, 100].tolist() == [ 255, 255, 255 ]


def test_to_strip_buffer() -> None:
	vision_frame = numpy.zeros((100, 200, 3), numpy.uint8)

	assert from_buffer(to_strip_buffer([ vision_frame, vision_frame ])).shape == (100, 400, 3)


def test_create_tile_frames() -> None:
	vision_frame = numpy.full((150, 200, 3), 255, numpy.uint8)
	tile_vision_frames, pad_width, pad_height = create_tile_frames(vision_frame, (64, 4, 2))

	assert len(tile_vision_frames) == 12
	assert pad_width == 244
	assert pad_height == 184
	assert get_first(tile_vision_frames).shape == (64, 64, 3)
	assert get_first(tile_vision_frames)[:6].max() == 0
	assert get_first(tile_vision_frames)[6, 6].tolist() == [ 255, 255, 255 ]
	assert get_first(tile_vision_frames)[6, 5].tolist() == [ 0, 0, 0 ]


def test_merge_tile_frames() -> None:
	vision_frame = numpy.random.default_rng(0).integers(0, 255, (150, 200, 3), dtype = numpy.uint8)

	for size in [ (64, 4, 2), (128, 8, 4), (32, 8, 4) ]:
		tile_vision_frames, pad_width, pad_height = create_tile_frames(vision_frame, size)

		assert numpy.array_equal(merge_tile_frames(tile_vision_frames, 200, 150, pad_width, pad_height, size), vision_frame) is True


def test_extract_vision_mask() -> None:
	vision_frame = numpy.zeros((2, 2, 4), numpy.uint8)
	vision_frame[:, :, 3] = 7

	assert extract_vision_mask(vision_frame).tolist() == [ [ 7, 7 ], [ 7, 7 ] ]
	assert extract_vision_mask(numpy.zeros((2, 2, 3), numpy.uint8)).tolist() == [ [ 255, 255 ], [ 255, 255 ] ]


def test_merge_vision_mask() -> None:
	vision_mask = numpy.full((2, 2), 9, numpy.uint8)

	assert merge_vision_mask(numpy.zeros((2, 2, 3), numpy.uint8), vision_mask).shape == (2, 2, 4)
	assert merge_vision_mask(numpy.zeros((2, 2, 4), numpy.uint8), vision_mask)[0, 0].tolist() == [ 0, 0, 0, 9 ]


def test_conditional_merge_vision_mask() -> None:
	vision_frame = numpy.zeros((2, 2, 3), numpy.uint8)

	assert conditional_merge_vision_mask(vision_frame, numpy.full((2, 2), 255, numpy.uint8)) is vision_frame
	assert conditional_merge_vision_mask(vision_frame, numpy.array([ [ 255, 255 ], [ 255, 254 ] ], numpy.uint8)).shape == (2, 2, 4)
