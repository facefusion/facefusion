from typing import List

import numpy

from facefusion.face_tracker import calculate_bounding_box_iou, get_anchor_indices, get_nearest_track_face, interpolate_array, interpolate_face, match_face_track, resolve_track_face
from facefusion.types import Face, FaceLandmarkSet


def create_face(bounding_box : List[float]) -> Face:
	x1, y1, x2, y2 = bounding_box
	center_y = (y1 + y2) / 2
	face_landmark_5 = numpy.array(
	[
		[ x1, y1 ],
		[ x2, y1 ],
		[ x1, y2 ],
		[ x2, y2 ],
		[ (x1 + x2) / 2, center_y ]
	], dtype = numpy.float64)
	face_landmark_68 = numpy.zeros((68, 2), dtype = numpy.float64)
	face_landmark_68[0] = [ x1, center_y ]
	face_landmark_68[16] = [ x2, center_y ]
	landmark_set : FaceLandmarkSet =\
	{
		'5': face_landmark_5,
		'5/68': face_landmark_5,
		'68': face_landmark_68,
		'68/5': face_landmark_68
	}
	return Face(
		bounding_box = numpy.array(bounding_box, dtype = numpy.float64),
		score_set =\
		{
			'detector': 1.0,
			'landmarker': 1.0
		},
		landmark_set = landmark_set,
		angle = 0,
		embedding = numpy.zeros(512, dtype = numpy.float64),
		embedding_norm = numpy.zeros(512, dtype = numpy.float64),
		age = range(25, 30),
		gender = 'male',
		race = 'white'
	)


def test_match_face_track() -> None:
	face_track =\
	{
		0 : create_face([ 10, 10, 50, 50 ])
	}

	assert match_face_track([ face_track ], create_face([ 12, 12, 52, 52 ]), 1, 0.3) is face_track
	assert match_face_track([ face_track ], create_face([ 200, 200, 240, 240 ]), 1, 0.3) == {}
	assert match_face_track([ face_track ], create_face([ 12, 12, 52, 52 ]), 0, 0.3) == {}


def test_calculate_bounding_box_iou() -> None:
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 0.0, 10.0, 10.0 ])) == 1.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 100.0, 100.0, 110.0, 110.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 20.0, 0.0, 30.0, 10.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 20.0, 10.0, 30.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 0.0, 10.0, 20.0 ])) == 0.5


def test_get_nearest_track_face() -> None:
	face_before = create_face([ 0, 0, 10, 10 ])
	face_after = create_face([ 90, 90, 100, 100 ])
	face_track =\
	{
		2 : face_before,
		8 : face_after
	}

	assert get_nearest_track_face(face_track, 3) is face_before
	assert get_nearest_track_face(face_track, 7) is face_after
	assert get_nearest_track_face(face_track, 5) is face_before
	assert get_nearest_track_face(
	{
		2 : face_before
	}, 9) is face_before


def test_get_anchor_indices() -> None:
	face_track =\
	{
		2 : create_face([ 0, 0, 10, 10 ]),
		8 : create_face([ 0, 0, 10, 10 ])
	}

	assert get_anchor_indices(face_track, 5) == (2, 8)
	assert get_anchor_indices(face_track, 1) == (-1, 2)
	assert get_anchor_indices(face_track, 9) == (8, -1)


def test_resolve_track_face() -> None:
	face_before = create_face([ 0, 0, 10, 10 ])
	face_target = create_face([ 40, 40, 50, 50 ])
	face_after = create_face([ 80, 80, 90, 90 ])

	assert resolve_track_face(
	{
		0 : face_before,
	  	5 : face_target,
		10 : face_after
	}, 5) is face_target
	assert resolve_track_face(
	{
		0 : face_before,
		10 : face_after
	}, 5).bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert resolve_track_face(
	{
		0 : face_before
	}, 5) is face_before
	assert resolve_track_face(
	{
		10 : face_after
	}, 5) is face_after


def test_interpolate_face() -> None:
	face_before = create_face([ 0, 0, 10, 10 ])
	face_after = create_face([ 80, 80, 90, 90 ])

	assert interpolate_face(face_before, face_after, 0.5).bounding_box.tolist() == [ 40.0, 40.0, 50.0, 50.0 ]
	assert interpolate_face(face_before, face_after, 0.5).angle == 0
	assert interpolate_face(face_before, face_after, 0.5).embedding is face_after.embedding
	assert interpolate_face(face_before, face_after, 0.25).embedding is face_before.embedding


def test_interpolate_array() -> None:
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 0.5).tolist() == [ 5.0, 10.0 ]
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 0.0).tolist() == [ 0.0, 0.0 ]
	assert interpolate_array(numpy.array([ 0.0, 0.0 ]), numpy.array([ 10.0, 20.0 ]), 1.0).tolist() == [ 10.0, 20.0 ]
