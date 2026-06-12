from functools import lru_cache
from typing import List, Optional, Tuple

import numpy
import scipy.linalg
import scipy.optimize

from facefusion.face_analyser import get_static_faces
from facefusion.hash_helper import create_hash
from facefusion.types import BoundingBox, Embedding, Face, KalmanCostMatrix, KalmanCovariance, KalmanMean, KalmanMeasurement, Track, TrackStore, VisionFrame

TRACK_STATE : List[Track] = []
TRACK_ID_COUNTER : List[int] = [ 0 ]
TRACK_STORE : TrackStore = {}


def track_frame(vision_frame : VisionFrame) -> None:
	faces = get_static_faces([ vision_frame ])
	assign_frame_tracks(vision_frame, faces)


def assign_frame_tracks(vision_frame : VisionFrame, faces : List[Face]) -> None:
	detection_bounding_boxes = [ face.bounding_box for face in faces ]
	detection_embeddings = [ face.embedding_norm for face in faces ]
	track_ids = update_tracks(detection_bounding_boxes, detection_embeddings)
	TRACK_STORE[create_hash(vision_frame.tobytes())] = list(zip(track_ids, detection_bounding_boxes))


def update_tracks(detection_bounding_boxes : List[BoundingBox], detection_embeddings : Optional[List[Embedding]] = None) -> List[int]:
	iou_threshold = 0.2
	embedding_max_distance = 0.4
	track_buffer = 30
	predicted_tracks = [ predict_track(track) for track in TRACK_STATE ]
	track_bounding_boxes = [kalman_measurement_to_bounding_box(track.mean) for track in predicted_tracks]
	iou_cost = calculate_iou_cost_matrix(track_bounding_boxes, detection_bounding_boxes)
	matches, unmatched_tracks, unmatched_detections = match_cost_matrix(iou_cost, 1.0 - iou_threshold)

	if detection_embeddings:
		track_embeddings = [ predicted_tracks[track_index].embedding for track_index in unmatched_tracks ]
		leftover_embeddings = [ detection_embeddings[detection_index] for detection_index in unmatched_detections ]
		embedding_cost = calculate_embedding_cost_matrix(track_embeddings, leftover_embeddings)
		embedding_matches, residual_tracks, residual_detections = match_cost_matrix(embedding_cost, embedding_max_distance)

		for sub_track_index, sub_detection_index in embedding_matches:
			matches.append((unmatched_tracks[sub_track_index], unmatched_detections[sub_detection_index]))
		unmatched_tracks = [ unmatched_tracks[sub_track_index] for sub_track_index in residual_tracks ]
		unmatched_detections = [ unmatched_detections[sub_detection_index] for sub_detection_index in residual_detections ]

	track_ids = [ 0 ] * len(detection_bounding_boxes)
	next_tracks : List[Track] = []

	for track_index, detection_index in matches:
		track = predicted_tracks[track_index]
		measurement = bounding_box_to_kalman_measurement(detection_bounding_boxes[detection_index])
		mean, covariance = kalman_update(track.mean, track.covariance, measurement)
		embedding = detection_embeddings[detection_index] if detection_embeddings else track.embedding
		next_tracks.append(track._replace(mean = mean, covariance = covariance, state = 'tracked', hit_streak = track.hit_streak + 1, time_since_update = 0, embedding = embedding))
		track_ids[detection_index] = track.track_id

	for track_index in unmatched_tracks:
		track = predicted_tracks[track_index]
		time_since_update = track.time_since_update + 1

		if time_since_update <= track_buffer:
			next_tracks.append(track._replace(state = 'lost', time_since_update = time_since_update))

	for detection_index in unmatched_detections:
		TRACK_ID_COUNTER[0] += 1
		measurement = bounding_box_to_kalman_measurement(detection_bounding_boxes[detection_index])
		mean, covariance = kalman_initiate(measurement)
		embedding = detection_embeddings[detection_index] if detection_embeddings else None
		next_tracks.append(Track(track_id = TRACK_ID_COUNTER[0], mean = mean, covariance = covariance, state = 'tracked', hit_streak = 1, time_since_update = 0, embedding = embedding))
		track_ids[detection_index] = TRACK_ID_COUNTER[0]

	TRACK_STATE[:] = next_tracks
	return track_ids


def lookup_frame_tracks(vision_frame : VisionFrame) -> Optional[List[Tuple[int, BoundingBox]]]:
	return TRACK_STORE.get(create_hash(vision_frame.tobytes()))


def clear_tracks() -> None:
	TRACK_STORE.clear()
	TRACK_STATE.clear()
	TRACK_ID_COUNTER[0] = 0


def predict_track(track : Track) -> Track:
	mean = track.mean.copy()

	if track.state == 'lost':
		mean[7] = 0
	mean, covariance = kalman_predict(mean, track.covariance)
	return track._replace(mean = mean, covariance = covariance)


def kalman_initiate(kalman_measurement : KalmanMeasurement) -> Tuple[KalmanMean, KalmanCovariance]:
	kalman_mean = numpy.r_[kalman_measurement, numpy.zeros_like(kalman_measurement)]
	standard_weight_position = 1.0 / 20
	standard_weight_velocity = 1.0 / 160
	standard_deviation =\
	[
		2 * standard_weight_position * kalman_measurement[3],
		2 * standard_weight_position * kalman_measurement[3],
		1e-2,
		2 * standard_weight_position * kalman_measurement[3],
		10 * standard_weight_velocity * kalman_measurement[3],
		10 * standard_weight_velocity * kalman_measurement[3],
		1e-5,
		10 * standard_weight_velocity * kalman_measurement[3]
	]
	kalman_covariance = numpy.diag(numpy.square(standard_deviation))
	return kalman_mean, kalman_covariance


def kalman_predict(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance) -> Tuple[KalmanMean, KalmanCovariance]:
	height = kalman_mean[3]
	standard_weight_position = 1.0 / 20
	standard_weight_velocity = 1.0 / 160
	standard_deviation_position = [ standard_weight_position * height, standard_weight_position * height, 1e-2, standard_weight_position * height ]
	standard_deviation_velocity = [ standard_weight_velocity * height, standard_weight_velocity * height, 1e-5, standard_weight_velocity * height ]
	motion_covariance = numpy.diag(numpy.square(numpy.r_[standard_deviation_position, standard_deviation_velocity]))
	motion_matrix = create_static_motion_matrix()
	kalman_mean = numpy.dot(kalman_mean, motion_matrix.T)
	kalman_covariance = numpy.linalg.multi_dot((motion_matrix, kalman_covariance, motion_matrix.T)) + motion_covariance
	return kalman_mean, kalman_covariance


def kalman_project(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance) -> Tuple[KalmanMeasurement, KalmanCovariance]:
	standard_weight_position = 1.0 / 20
	standard_deviation =\
	[
		standard_weight_position * kalman_mean[3],
	  	standard_weight_position * kalman_mean[3],
		1e-1,
		standard_weight_position * kalman_mean[3]
	]
	innovation_covariance = numpy.diag(numpy.square(standard_deviation))
	update_matrix = numpy.eye(4, 8)
	projected_mean = numpy.dot(update_matrix, kalman_mean)
	projected_covariance = numpy.linalg.multi_dot((update_matrix, kalman_covariance, update_matrix.T))
	return projected_mean, projected_covariance + innovation_covariance


def kalman_update(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance, kalman_measurement : KalmanMeasurement) -> Tuple[KalmanMean, KalmanCovariance]:
	projected_mean, projected_covariance = kalman_project(kalman_mean, kalman_covariance)
	chol_factor, lower = scipy.linalg.cho_factor(projected_covariance, lower = True, check_finite = False)
	update_matrix = numpy.eye(4, 8)
	kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), numpy.dot(kalman_covariance, update_matrix.T).T, check_finite = False).T
	innovation = kalman_measurement - projected_mean
	kalman_mean = kalman_mean + numpy.dot(innovation, kalman_gain.T)
	kalman_covariance = kalman_covariance - numpy.linalg.multi_dot((kalman_gain, projected_covariance, kalman_gain.T))
	return kalman_mean, kalman_covariance


@lru_cache()
def create_static_motion_matrix() -> numpy.ndarray:
	motion_matrix = numpy.eye(8, 8)

	for index in range(4):
		motion_matrix[index, 4 + index] = 1.0
	return motion_matrix


def bounding_box_to_kalman_measurement(bounding_box : BoundingBox) -> KalmanMeasurement:
	width = bounding_box[2] - bounding_box[0]
	height = bounding_box[3] - bounding_box[1]
	center_x = bounding_box[0] + width / 2
	center_y = bounding_box[1] + height / 2
	return numpy.array([ center_x, center_y, width / height, height ])


def kalman_measurement_to_bounding_box(kalman_mean : KalmanMean) -> BoundingBox:
	height = kalman_mean[3]
	width = kalman_mean[2] * height
	center_x = kalman_mean[0]
	center_y = kalman_mean[1]
	return numpy.array([ center_x - width / 2, center_y - height / 2, center_x + width / 2, center_y + height / 2 ])


def calculate_iou(bounding_box_1 : BoundingBox, bounding_box_2 : BoundingBox) -> float:
	intersection_left = max(bounding_box_1[0], bounding_box_2[0])
	intersection_top = max(bounding_box_1[1], bounding_box_2[1])
	intersection_right = min(bounding_box_1[2], bounding_box_2[2])
	intersection_bottom = min(bounding_box_1[3], bounding_box_2[3])
	intersection_width = max(intersection_right - intersection_left, 0)
	intersection_height = max(intersection_bottom - intersection_top, 0)
	intersection_area = intersection_width * intersection_height
	area_1 = (bounding_box_1[2] - bounding_box_1[0]) * (bounding_box_1[3] - bounding_box_1[1])
	area_2 = (bounding_box_2[2] - bounding_box_2[0]) * (bounding_box_2[3] - bounding_box_2[1])
	union_area = area_1 + area_2 - intersection_area

	if union_area > 0:
		return intersection_area / union_area

	return 0.0


def calculate_iou_cost_matrix(track_bounding_boxes : List[BoundingBox], detection_bounding_boxes : List[BoundingBox]) -> KalmanCostMatrix:
	cost_matrix = numpy.ones((len(track_bounding_boxes), len(detection_bounding_boxes)))

	for track_index, track_bounding_box in enumerate(track_bounding_boxes):

		for detection_index, detection_bounding_box in enumerate(detection_bounding_boxes):
			cost_matrix[track_index, detection_index] = 1.0 - calculate_iou(track_bounding_box, detection_bounding_box)

	return cost_matrix


def calculate_embedding_cost_matrix(track_embeddings : List[Embedding], detection_embeddings : List[Embedding]) -> KalmanCostMatrix:
	cost_matrix = numpy.ones((len(track_embeddings), len(detection_embeddings)))

	for track_index, track_embedding in enumerate(track_embeddings):

		for detection_index, detection_embedding in enumerate(detection_embeddings):
			cost_matrix[track_index, detection_index] = numpy.interp(1.0 - numpy.dot(track_embedding, detection_embedding), [ 0, 2 ], [ 0, 1 ])

	return cost_matrix


def match_cost_matrix(cost_matrix : KalmanCostMatrix, max_distance : float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
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
