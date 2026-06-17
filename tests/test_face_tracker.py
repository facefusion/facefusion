import numpy

from facefusion.face_helper import calculate_bounding_box_iou
from facefusion.face_tracker import get_anchor_indices, match_face_track, resolve_track_face
from tests.helper import create_face_from_bounding_box


def test_match_face_track() -> None:
	face_track =\
	{
		0 : create_face_from_bounding_box([10, 10, 50, 50])
	}

	assert match_face_track([ face_track ], create_face_from_bounding_box([12, 12, 52, 52]), 1, 0.3) is face_track
	assert match_face_track([ face_track ], create_face_from_bounding_box([200, 200, 240, 240]), 1, 0.3) == {}
	assert match_face_track([ face_track ], create_face_from_bounding_box([12, 12, 52, 52]), 0, 0.3) == {}


def test_calculate_bounding_box_iou() -> None:
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 0.0, 10.0, 10.0 ])) == 1.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 100.0, 100.0, 110.0, 110.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 20.0, 0.0, 30.0, 10.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 20.0, 10.0, 30.0 ])) == 0.0
	assert calculate_bounding_box_iou(numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 0.0, 0.0, 10.0, 20.0 ])) == 0.5


def test_get_anchor_indices() -> None:
	face_track =\
	{
		2 : create_face_from_bounding_box([0, 0, 10, 10]),
		8 : create_face_from_bounding_box([0, 0, 10, 10])
	}

	assert get_anchor_indices(face_track, 5) == (2, 8)
	assert get_anchor_indices(face_track, 1) == (-1, 2)
	assert get_anchor_indices(face_track, 9) == (8, -1)


def test_resolve_track_face() -> None:
	face_before = create_face_from_bounding_box([0, 0, 10, 10])
	face_target = create_face_from_bounding_box([40, 40, 50, 50])
	face_after = create_face_from_bounding_box([80, 80, 90, 90])

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
