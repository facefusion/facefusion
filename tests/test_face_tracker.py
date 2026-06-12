import numpy
import pytest

from facefusion import state_manager
from facefusion.face_selector import bridge_reference_by_track, order_faces_by_track, resolve_target_faces
from facefusion.face_store import clear_faces, set_faces
from facefusion.face_tracker import assign_frame_tracks, clear_tracks, lookup_frame_tracks, track_frame, update_tracks
from facefusion.types import Face


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_tracks()
	clear_faces()


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


def test_track_frame() -> None:
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	set_faces(vision_frame, [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ])
	track_frame(vision_frame)

	assert [ track_id for track_id, _ in lookup_frame_tracks(vision_frame) ] == [ 1 ]


def test_clear_tracks() -> None:
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	assign_frame_tracks(vision_frame, [ create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ])) ])
	clear_tracks()

	assert lookup_frame_tracks(vision_frame) is None


def test_resolve_target_faces() -> None:
	state_manager.init_item('face_tracking', True)
	vision_frame = numpy.ones((4, 4, 3), dtype = numpy.uint8)
	face = create_face(numpy.array([ 0.0, 0.0, 100.0, 100.0 ]))
	set_faces(vision_frame, [ face ])

	assert numpy.array_equal(resolve_target_faces(vision_frame)[0].bounding_box, face.bounding_box)


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
