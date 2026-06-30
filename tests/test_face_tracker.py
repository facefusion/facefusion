import numpy
import pytest

from facefusion import face_classifier, face_detector, face_landmarker, face_recognizer, state_manager
from facefusion.common_helper import get_first, get_last
from facefusion.download import conditional_download
from facefusion.face_creator import get_many_faces, get_one_face
from facefusion.face_store import clear_faces
from facefusion.face_tracker import create_face_tracks, select_face_track, track_faces
from facefusion.vision import read_static_video_chunk, read_static_video_frame
from .helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
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
	state_manager.init_item('face_landmarker_model', 'many')
	state_manager.init_item('face_landmarker_score', 0.5)
	state_manager.init_item('face_tracker_score', 0.3)

	face_classifier.pre_check()
	face_detector.pre_check()
	face_landmarker.pre_check()
	face_recognizer.pre_check()


@pytest.fixture(autouse = True)
def before_each() -> None:
	face_classifier.clear_inference_pool()
	face_detector.clear_inference_pool()
	face_landmarker.clear_inference_pool()
	face_recognizer.clear_inference_pool()
	clear_faces()


def test_track_faces() -> None:
	target_path = get_test_example_file('target-240p.mp4')
	video_frame_chunk = read_static_video_chunk(target_path, 0, 7)
	target_vision_frames = [ video_frame_chunk.get(frame_number) for frame_number in sorted(video_frame_chunk) ]
	empty_vision_frame = numpy.zeros_like(get_first(target_vision_frames))

	target_vision_frames[2] = empty_vision_frame
	target_vision_frames[3] = empty_vision_frame
	target_vision_frames[4] = empty_vision_frame
	target_vision_frames[5] = empty_vision_frame

	assert len(track_faces(target_vision_frames, 0.3)) == 1

	target_vision_frames = [ video_frame_chunk.get(frame_number) for frame_number in sorted(video_frame_chunk)[:5] ]
	target_vision_frames[0] = empty_vision_frame
	target_vision_frames[1] = empty_vision_frame
	target_vision_frames[2] = empty_vision_frame

	assert len(track_faces(target_vision_frames, 0.3)) == 0


def test_create_face_tracks() -> None:
	target_vision_frame = read_static_video_frame(get_test_example_file('target-240p.mp4'), 0)
	multi_face_vision_frame = numpy.hstack([ target_vision_frame, target_vision_frame ])

	face_tracks = create_face_tracks([ target_vision_frame, target_vision_frame ], 0.3)

	assert len(face_tracks) == 1
	assert sorted(get_first(face_tracks)) == [ 0, 1 ]

	face_tracks = create_face_tracks([ multi_face_vision_frame, multi_face_vision_frame ], 0.3)

	assert len(face_tracks) == 2
	assert sorted(get_first(face_tracks)) == [ 0, 1 ]
	assert sorted(get_last(face_tracks)) == [ 0, 1 ]

	assert len(create_face_tracks([ target_vision_frame, target_vision_frame ], 1.0)) == 2


def test_select_face_track() -> None:
	target_vision_frame = read_static_video_frame(get_test_example_file('target-240p.mp4'), 0)
	face = get_one_face(get_many_faces([ target_vision_frame ]))
	face_overlap = face._replace(bounding_box = numpy.array([ 12, 12, 52, 52 ]))
	face_distant = face._replace(bounding_box = numpy.array([ 200, 200, 240, 240 ]))
	face_track_overlap =\
	{
		0 : face._replace(bounding_box = numpy.array([ 10, 10, 50, 50 ]))
	}
	face_track_distant =\
	{
		0 : face._replace(bounding_box = numpy.array([ 100, 100, 140, 140 ]))
	}

	assert select_face_track([ face_track_overlap, face_track_distant ], face_overlap, 0.3) is face_track_overlap
	assert select_face_track([ face_track_overlap, face_track_distant ], face_distant, 0.3) == {}
