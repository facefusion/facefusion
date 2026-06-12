from typing import List, Optional, Tuple

import numpy

from facefusion.face_analyser import get_static_faces
from facefusion.face_tracker_helper import calculate_embedding_cost_matrix, calculate_iou_cost_matrix, match_cost_matrix
from facefusion.hash_helper import create_hash
from facefusion.kalman_filter import kalman_initiate, kalman_predict, kalman_update
from facefusion.types import BoundingBox, Embedding, Face, FaceTrack, FaceTrackStore, KalmanMean, KalmanMeasurement, VisionFrame

FACE_TRACK_STATE : List[FaceTrack] = []
FACE_TRACK_ID_COUNTER : List[int] = [ 0 ]
FACE_TRACK_STORE : FaceTrackStore = {}


def track_frame(vision_frame : VisionFrame) -> None:
	faces = get_static_faces([ vision_frame ])
	assign_frame_tracks(vision_frame, faces)


def assign_frame_tracks(vision_frame : VisionFrame, faces : List[Face]) -> None:
	detection_bounding_boxes = [ face.bounding_box for face in faces ]
	detection_embeddings = [ face.embedding_norm for face in faces ]
	track_ids = update_tracks(detection_bounding_boxes, detection_embeddings)
	FACE_TRACK_STORE[create_hash(vision_frame.tobytes())] = list(zip(track_ids, detection_bounding_boxes))


def update_tracks(detection_bounding_boxes : List[BoundingBox], detection_embeddings : Optional[List[Embedding]] = None) -> List[int]:
	iou_threshold = 0.2
	embedding_max_distance = 0.4
	track_buffer = 30
	predicted_tracks = [ predict_track(track) for track in FACE_TRACK_STATE ]
	matches, unmatched_tracks, unmatched_detections = match_tracks_to_detections(predicted_tracks, detection_bounding_boxes, detection_embeddings, iou_threshold, embedding_max_distance)
	stepped_tracks, stepped_track_ids = step_matched_tracks(predicted_tracks, matches, detection_bounding_boxes, detection_embeddings)
	aged_tracks = age_unmatched_tracks(predicted_tracks, unmatched_tracks, track_buffer)
	spawned_tracks, spawned_track_ids = spawn_new_tracks(unmatched_detections, detection_bounding_boxes, detection_embeddings)
	track_ids = [ 0 ] * len(detection_bounding_boxes)

	for detection_index, track_id in stepped_track_ids + spawned_track_ids:
		track_ids[detection_index] = track_id

	FACE_TRACK_STATE[:] = stepped_tracks + aged_tracks + spawned_tracks
	return track_ids


def lookup_frame_tracks(vision_frame : VisionFrame) -> Optional[List[Tuple[int, BoundingBox]]]:
	return FACE_TRACK_STORE.get(create_hash(vision_frame.tobytes()))


def clear_tracks() -> None:
	FACE_TRACK_STORE.clear()
	FACE_TRACK_STATE.clear()
	FACE_TRACK_ID_COUNTER[0] = 0


def predict_track(track : FaceTrack) -> FaceTrack:
	mean = track.mean.copy()
	height_velocity_index = 7

	if track.state == 'lost':
		mean[height_velocity_index] = 0
	mean, covariance = kalman_predict(mean, track.covariance)
	return track._replace(mean = mean, covariance = covariance)


def match_tracks_to_detections(predicted_tracks : List[FaceTrack], detection_bounding_boxes : List[BoundingBox], detection_embeddings : Optional[List[Embedding]], iou_threshold : float, embedding_max_distance : float) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
	track_bounding_boxes = [ kalman_measurement_to_bounding_box(track.mean) for track in predicted_tracks ]
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

	return matches, unmatched_tracks, unmatched_detections


def step_matched_tracks(predicted_tracks : List[FaceTrack], matches : List[Tuple[int, int]], detection_bounding_boxes : List[BoundingBox], detection_embeddings : Optional[List[Embedding]]) -> Tuple[List[FaceTrack], List[Tuple[int, int]]]:
	stepped_tracks : List[FaceTrack] = []
	track_ids : List[Tuple[int, int]] = []

	for track_index, detection_index in matches:
		track = predicted_tracks[track_index]
		measurement = bounding_box_to_kalman_measurement(detection_bounding_boxes[detection_index])
		mean, covariance = kalman_update(track.mean, track.covariance, measurement)
		embedding = detection_embeddings[detection_index] if detection_embeddings else track.embedding
		stepped_tracks.append(track._replace(mean = mean, covariance = covariance, state = 'tracked', hit_streak = track.hit_streak + 1, time_since_update = 0, embedding = embedding))
		track_ids.append((detection_index, track.track_id))

	return stepped_tracks, track_ids


def age_unmatched_tracks(predicted_tracks : List[FaceTrack], unmatched_tracks : List[int], track_buffer : int) -> List[FaceTrack]:
	aged_tracks : List[FaceTrack] = []

	for track_index in unmatched_tracks:
		track = predicted_tracks[track_index]
		time_since_update = track.time_since_update + 1

		if time_since_update <= track_buffer:
			aged_tracks.append(track._replace(state = 'lost', time_since_update = time_since_update))

	return aged_tracks


def spawn_new_tracks(unmatched_detections : List[int], detection_bounding_boxes : List[BoundingBox], detection_embeddings : Optional[List[Embedding]]) -> Tuple[List[FaceTrack], List[Tuple[int, int]]]:
	spawned_tracks : List[FaceTrack] = []
	track_ids : List[Tuple[int, int]] = []

	for detection_index in unmatched_detections:
		FACE_TRACK_ID_COUNTER[0] += 1
		measurement = bounding_box_to_kalman_measurement(detection_bounding_boxes[detection_index])
		mean, covariance = kalman_initiate(measurement)
		embedding = detection_embeddings[detection_index] if detection_embeddings else None
		spawned_tracks.append(FaceTrack(track_id = FACE_TRACK_ID_COUNTER[0], mean = mean, covariance = covariance, state = 'tracked', hit_streak = 1, time_since_update = 0, embedding = embedding))
		track_ids.append((detection_index, FACE_TRACK_ID_COUNTER[0]))

	return spawned_tracks, track_ids


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
