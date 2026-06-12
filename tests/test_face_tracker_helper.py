import numpy

from facefusion.face_tracker_helper import calculate_embedding_cost_matrix, calculate_iou_cost_matrix, match_cost_matrix


def test_calculate_iou_cost_matrix() -> None:
	cost_matrix = calculate_iou_cost_matrix([ numpy.array([ 0.0, 0.0, 10.0, 10.0 ]) ], [ numpy.array([ 0.0, 0.0, 10.0, 10.0 ]), numpy.array([ 100.0, 100.0, 110.0, 110.0 ]) ])

	assert cost_matrix[0][0] == 0.0
	assert cost_matrix[0][1] == 1.0


def test_calculate_embedding_cost_matrix() -> None:
	embedding_a = numpy.array([ 1.0, 0.0 ])
	embedding_b = numpy.array([ -1.0, 0.0 ])
	cost_matrix = calculate_embedding_cost_matrix([ embedding_a ], [ embedding_a, embedding_b ])

	assert cost_matrix[0][0] == 0.0
	assert cost_matrix[0][1] == 1.0


def test_associate() -> None:
	matches, unmatched_tracks, unmatched_detections = match_cost_matrix(numpy.array([ [ 0.0, 1.0 ], [ 1.0, 0.1 ] ]), 0.8)

	assert matches == [ (0, 0), (1, 1) ]
	assert unmatched_tracks == []
	assert unmatched_detections == []


def test_associate_rejects_above_distance() -> None:
	matches, unmatched_tracks, unmatched_detections = match_cost_matrix(numpy.array([ [ 0.9 ] ]), 0.8)

	assert matches == []
	assert unmatched_tracks == [ 0 ]
	assert unmatched_detections == [ 0 ]
