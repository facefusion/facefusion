from io import BytesIO
from typing import Iterator
from unittest.mock import patch

import pytest
from starlette.datastructures import UploadFile

from facefusion import face_aligner, face_classifier, face_detector, face_recognizer, inference_manager, session_context, state_manager, video_manager
from facefusion.apis.asset_helper import capture_asset_faces, capture_asset_frames, detect_media_type_by_format, detect_media_type_by_path, extract_image_metadata, read_asset_frames, validate_asset_files, validate_frame_resolution
from facefusion.apis.asset_store import create_asset, init
from facefusion.download import conditional_download
from facefusion.types import AudioAsset, ImageAsset, VideoAsset
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	inference_manager.init()
	video_manager.init()

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github' ])
	state_manager.init_item('face_detector_angles', [ 0 ])
	state_manager.init_item('face_detector_model', 'yolo_face')
	state_manager.init_item('face_detector_size', '640x640')
	state_manager.init_item('face_detector_margin', (0, 0, 0, 0))
	state_manager.init_item('face_detector_score', 0.5)
	state_manager.init_item('face_aligner_model', 'many')
	state_manager.init_item('face_aligner_score', 0.5)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_aligner.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> Iterator[None]:
	local_id = session_context.resolve_local_id()

	session_context.set_session_id(local_id)
	init()

	yield

	session_context.set_session_id(local_id)


def test_detect_media_type() -> None:
	assert detect_media_type_by_path(get_test_example_file('source.jpg')) == 'image'
	assert detect_media_type_by_path(get_test_example_file('target-240p.mp4')) == 'video'
	assert detect_media_type_by_path(get_test_example_file('source.mp3')) == 'audio'
	assert detect_media_type_by_path('invalid') is None


def test_extract_image_metadata() -> None:
	image_metadata = extract_image_metadata(get_test_example_file('source.jpg'))

	assert image_metadata.get('resolution') == (1024, 1024)


def test_detect_media_type_by_format() -> None:
	assert detect_media_type_by_format('mp3') == 'audio'
	assert detect_media_type_by_format('jpeg') == 'image'
	assert detect_media_type_by_format('mp4') == 'video'
	assert detect_media_type_by_format('invalid') is None


def test_validate_asset_files() -> None:
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.jpg') ]) is True
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.mp3') ]) is True
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'target-240p.mp4') ]) is True
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'invalid') ]) is False
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.exe') ]) is False
	assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.exe'), UploadFile(BytesIO(), filename = 'source.jpg') ]) is False
	assert validate_asset_files([]) is True

	with patch('facefusion.ffmpeg.get_static_available_encoder_set', return_value =
	{
		'audio': [],
		'image': [],
		'video': []
	}):
		assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.jpg') ]) is False
		assert validate_asset_files([ UploadFile(BytesIO(), filename = 'source.mp3') ]) is False
		assert validate_asset_files([ UploadFile(BytesIO(), filename = 'target-240p.mp4') ]) is False


def test_validate_frame_resolution() -> None:
	assert validate_frame_resolution('128x128') is True
	assert validate_frame_resolution('65x4095') is True
	assert validate_frame_resolution('64x128') is False
	assert validate_frame_resolution('128x64') is False
	assert validate_frame_resolution('4096x128') is False
	assert validate_frame_resolution('128x4096') is False
	assert validate_frame_resolution('invalid') is False
	assert validate_frame_resolution('') is False
	assert validate_frame_resolution(None) is False


def test_read_asset_frames() -> None:
	image_asset : ImageAsset = create_asset('source', get_test_example_file('source.jpg')) #type:ignore[assignment]
	video_asset : VideoAsset = create_asset('target', get_test_example_file('target-240p.mp4')) #type:ignore[assignment]
	audio_asset : AudioAsset = create_asset('source', get_test_example_file('source.mp3')) #type:ignore[assignment]

	assert len(read_asset_frames(image_asset, [])) == 1
	assert read_asset_frames(image_asset, [])[0].shape == (1024, 1024, 3)
	assert read_asset_frames(video_asset, []) == []
	assert len(read_asset_frames(video_asset, [ '0', '10' ])) == 2
	assert read_asset_frames(video_asset, [ '0' ])[0].shape == (226, 426, 3)
	assert read_asset_frames(video_asset, [ 'invalid', '-1' ]) == []
	assert read_asset_frames(audio_asset, [ '0' ]) == [] #type:ignore[arg-type]


def test_capture_asset_frames() -> None:
	image_asset : ImageAsset = create_asset('source', get_test_example_file('source.jpg')) #type:ignore[assignment]
	video_asset : VideoAsset = create_asset('target', get_test_example_file('target-240p.mp4')) #type:ignore[assignment]
	capture_vision_frames = capture_asset_frames(image_asset, [], '128x256')

	assert len(capture_vision_frames) == 1
	assert capture_vision_frames[0].shape == (256, 128, 3)

	capture_vision_frames = capture_asset_frames(video_asset, [ '0', '1' ], '256x256')

	assert len(capture_vision_frames) == 2
	assert capture_vision_frames[1].shape == (256, 256, 3)


def test_capture_asset_faces() -> None:
	image_asset : ImageAsset = create_asset('source', get_test_example_file('source.jpg')) #type:ignore[assignment]
	video_asset : VideoAsset = create_asset('target', get_test_example_file('target-240p.mp4')) #type:ignore[assignment]
	capture_vision_frames = capture_asset_faces(image_asset, [], '128x256')

	assert len(capture_vision_frames) == 1
	assert capture_vision_frames[0].shape == (256, 128, 3)

	capture_vision_frames = capture_asset_faces(video_asset, [ '0', '1' ], '256x256')

	assert len(capture_vision_frames) == 2
	assert capture_vision_frames[1].shape == (256, 256, 3)
	assert capture_asset_faces(video_asset, [ 'invalid' ], '256x256') == []
