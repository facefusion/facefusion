import numpy
import pytest

from facefusion import state_manager
from facefusion.face_selector import bridge_reference_by_track, order_faces_by_track, resolve_target_faces
from facefusion.face_tracker import assign_frame_tracks, associate, clear_tracks, embedding_distance, get_target_faces, has_target_faces, iou_distance, kalman_initiate, kalman_predict, kalman_update, lookup_frame_tracks, set_target_faces, update_tracks
from facefusion.types import Face


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_tracks()


def moving_bounding_box(left : float, speed : float, frame_number : int) -> numpy.ndarray:
	position = left + speed * frame_number
	return numpy.array([ position, 0.0, position + 100.0, 100.0 ])


def create_face(bounding_box : numpy.ndarray) -> Face:
	return Face(
		bounding_box = bounding_box,
		score_set = { 'detector': 0.9, 'landmarker': 0.9 },
		landmark_set = {},
		angle = 0,
		embedding = numpy.zeros(512),
		embedding_norm = numpy.zeros(512),
		age = range(20, 30),
		gender = 'male',
		race = 'white'
	)


def test_kalman_predict() -> None:
	mean, covariance = kalman_initiate(numpy.array([ 200.0, 360.0, 0.75, 240.0 ]))
	center_x = 200.0

	for _ in range(40):
		mean, covariance = kalman_predict(mean, covariance)
		center_x += 9.0
		mean, covariance = kalman_update(mean, covariance, numpy.array([ center_x, 360.0, 0.75, 240.0 ]))

	assert round(mean[4]) == 9


def test_iou_distance() -> None:
	cost_matrix = iou_distance([ numpy.array([ 0.0, 0.0, 10.0, 10.0 ]) ], [ numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 100.0, 100.0, 110.0, 110.0 ]) ])

	assert cost_matrix[0][0] == 0.0
	assert cost_matrix[0][1] == 1.0


def test_embedding_distance() -> None:
	embedding_a = numpy.array([ 1.0, 0.0 ])
	embedding_b = numpy.array([ -1.0, 0.0 ])
	cost_matrix = embedding_distance([ embedding_a ], [ embedding_a, embedding_b ])

	assert cost_matrix[0][0] == 0.0
	assert cost_matrix[0][1] == 1.0


def test_associate() -> None:
	matches, unmatched_tracks, unmatched_detections = associate(numpy.array([ [ 0.0, 1.0 ], [ 1.0, 0.1 ] ]), 0.8)

	assert matches == [ (0, 0), (1, 1) ]
	assert unmatched_tracks == []
	assert unmatched_detections == []


def test_associate_rejects_above_distance() -> None:
	matches, unmatched_tracks, unmatched_detections = associate(numpy.array([ [ 0.9 ] ]), 0.8)

	assert matches == []
	assert unmatched_tracks == [ 0 ]
	assert unmatched_detections == [ 0 ]


def test_update_tracks() -> None:
	for frame_number in range(5):
		track_ids = update_tracks([ moving_bounding_box(0.0, 20.0, frame_number) ])

	assert track_ids == [ 1 ]


def test_update_tracks_assigns_new_id() -> None:
	update_tracks([ numpy.array([ 0.0, 0.0, 100.0, 100.0 ]) ])
	track_ids = update_tracks([ numpy.array([ 500.0, 500.0, 600.0, 600.0 ]) ])

	assert track_ids == [ 2 ]


def test_update_tracks_recovers_id_after_occlusion() -> None:
	for frame_number in range(10):
		update_tracks([ moving_bounding_box(0.0, 20.0, frame_number) ])

	for frame_number in range(10, 13):
		update_tracks([])

	track_ids = update_tracks([ moving_bounding_box(0.0, 20.0, 13) ])

	assert track_ids == [ 1 ]


def test_update_tracks_follows_box_when_order_swaps() -> None:
	track_ids = update_tracks([ numpy.array([ 0.0, 0.0, 100.0, 100.0 ]), numpy.array([ 300.0, 0.0, 400.0, 100.0 ]) ])
	assert track_ids == [ 1, 2 ]

	track_ids = update_tracks([ numpy.array([ 305.0, 0.0, 405.0, 100.0 ]), numpy.array([ 5.0, 0.0, 105.0, 100.0 ]) ])
	assert track_ids == [ 2, 1 ]


def test_update_tracks_embedding_rescue() -> None:
	embedding = numpy.array([ 1.0, 0.0 ])
	update_tracks([ numpy.array([ 0.0, 0.0, 100.0, 100.0 ]) ], [ embedding ])
	track_ids = update_tracks([ numpy.array([ 500.0, 0.0, 600.0, 100.0 ]) ], [ embedding ])

	assert track_ids == [ 1 ]


def test_update_tracks_embedding_rejects_mismatch() -> None:
	update_tracks([ numpy.array([ 0.0, 0.0, 100.0, 100.0 ]) ], [ numpy.array([ 1.0, 0.0 ]) ])
	track_ids = update_tracks([ numpy.array([ 500.0, 0.0, 600.0, 100.0 ]) ], [ numpy.array([ -1.0, 0.0 ]) ])

	assert track_ids == [ 2 ]


def test_assign_frame_tracks() -> None:
	vision_frame = numpy.zeros((4, 4, 3), dtype = numpy.uint8)
	assign_frame_tracks(vision_frame, [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])), create_face(numpy.array([ 300.0, 0.0, 400.0, 100.0 ])) ])
	frame_tracks = lookup_frame_tracks(vision_frame)

	assert [ track_id for track_id, _ in frame_tracks ] == [ 1, 2 ]


def test_lookup_frame_tracks() -> None:
	assert lookup_frame_tracks(numpy.ones((4, 4, 3), dtype = numpy.uint8)) is None


def test_has_target_faces() -> None:
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	set_target_faces(vision_frame, [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ])

	assert has_target_faces(vision_frame) is True
	assert has_target_faces(numpy.full((4, 4, 3), 2, dtype = numpy.uint8)) is False
	assert has_target_faces(numpy.zeros((4, 4, 3), dtype = numpy.uint8)) is False


def test_get_target_faces() -> None:
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	assert get_target_faces(vision_frame) is None

	faces = [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ]
	set_target_faces(vision_frame, faces)
	assert get_target_faces(vision_frame) is faces


def test_set_target_faces() -> None:
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	faces = [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ]
	set_target_faces(vision_frame, faces)

	assert get_target_faces(vision_frame) is faces


def test_resolve_target_faces() -> None:
	state_manager.init_item('face_tracking', True)
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	faces = [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ]
	set_target_faces(vision_frame, faces)

	assert resolve_target_faces(vision_frame) is faces


def test_order_faces_by_track() -> None:
	vision_frame = numpy.zeros((4, 4, 3), dtype = numpy.uint8)
	face_left = create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ]))
	face_right = create_face(numpy.array([ 300.0, 0.0, 400.0, 100.0 ]))
	assign_frame_tracks(vision_frame, [ face_left, face_right ])
	ordered_faces = order_faces_by_track(vision_frame, [ face_right, face_left ])

	assert numpy.array_equal(ordered_faces[0].bounding_box, face_left.bounding_box)
	assert numpy.array_equal(ordered_faces[1].bounding_box, face_right.bounding_box)


def test_bridge_reference_by_track() -> None:
	reference_frame = numpy.zeros((4, 4, 3), dtype = numpy.uint8)
	target_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	reference_face = create_face(numpy.array([ 100.0, 100.0, 200.0, 200.0 ]))
	target_face_a = create_face(numpy.array([ 100.0, 100.0, 200.0, 200.0 ]))
	target_face_b = create_face(numpy.array([ 400.0, 100.0, 500.0, 200.0 ]))
	assign_frame_tracks(reference_frame, [ reference_face ])
	assign_frame_tracks(target_frame, [ target_face_a, target_face_b ])

	bridged_faces = bridge_reference_by_track(reference_frame, reference_face, target_frame, [ target_face_a, target_face_b ], [])
	assert len(bridged_faces) == 1
	assert numpy.array_equal(bridged_faces[0].bounding_box, target_face_a.bounding_box)

	bridged_faces = bridge_reference_by_track(reference_frame, reference_face, target_frame, [ target_face_a, target_face_b ], [ target_face_b ])
	assert len(bridged_faces) == 1
	assert numpy.array_equal(bridged_faces[0].bounding_box, target_face_b.bounding_box)
