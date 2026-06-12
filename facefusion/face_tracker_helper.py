from typing import List, Tuple

import numpy
import scipy.optimize

from facefusion.face_helper import calculate_iou
from facefusion.types import BoundingBox, CostMatrix, Embedding


def calculate_iou_cost_matrix(track_bounding_boxes : List[BoundingBox], detection_bounding_boxes : List[BoundingBox]) -> CostMatrix:
	cost_matrix = numpy.ones((len(track_bounding_boxes), len(detection_bounding_boxes)))

	for track_index, track_bounding_box in enumerate(track_bounding_boxes):

		for detection_index, detection_bounding_box in enumerate(detection_bounding_boxes):
			cost_matrix[track_index, detection_index] = 1.0 - calculate_iou(track_bounding_box, detection_bounding_box)

	return cost_matrix


def calculate_embedding_cost_matrix(track_embeddings : List[Embedding], detection_embeddings : List[Embedding]) -> CostMatrix:
	cost_matrix = numpy.ones((len(track_embeddings), len(detection_embeddings)))

	for track_index, track_embedding in enumerate(track_embeddings):

		for detection_index, detection_embedding in enumerate(detection_embeddings):
			cost_matrix[track_index, detection_index] = numpy.interp(1.0 - numpy.dot(track_embedding, detection_embedding), [ 0, 2 ], [ 0, 1 ])

	return cost_matrix


def match_cost_matrix(cost_matrix : CostMatrix, max_distance : float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
	matches : List[Tuple[int, int]] = []
	unmatched_tracks = list(range(cost_matrix.shape[0]))
	unmatched_detections = list(range(cost_matrix.shape[1]))

	if cost_matrix.size:
		track_indices, detection_indices = scipy.optimize.linear_sum_assignment(cost_matrix)

		for track_index, detection_index in zip(track_indices, detection_indices):
			if cost_matrix[track_index, detection_index] <= max_distance:
				matches.append((int(track_index), int(detection_index)))
				unmatched_tracks.remove(int(track_index))
				unmatched_detections.remove(int(detection_index))

	return matches, unmatched_tracks, unmatched_detections
