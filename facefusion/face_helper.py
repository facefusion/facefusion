from functools import lru_cache
from typing import List, Sequence, Tuple

import cv2
import numpy
from cv2.typing import Size

from facefusion.types import Anchors, Angle, BoundingBox, Distance, FaceDetectorModel, FaceLandmark5, FaceLandmark68, Mask, Matrix, Points, Scale, Score, Translation, VisionFrame, WarpTemplate, WarpTemplateSet

WARP_TEMPLATE_SET : WarpTemplateSet =\
{
	'arcface_112_v1': numpy.array(
	[
		[ 0.35473214, 0.45658929 ],
		[ 0.64526786, 0.45658929 ],
		[ 0.50000000, 0.61154464 ],
		[ 0.37913393, 0.77687500 ],
		[ 0.62086607, 0.77687500 ]
	]),
	'arcface_112_v2': numpy.array(
	[
		[ 0.34191607, 0.46157411 ],
		[ 0.65653393, 0.45983393 ],
		[ 0.50022500, 0.64050536 ],
		[ 0.37097589, 0.82469196 ],
		[ 0.63151696, 0.82325089 ]
	]),
	'arcface_128': numpy.array(
	[
		[ 0.36167656, 0.40387734 ],
		[ 0.63696719, 0.40235469 ],
		[ 0.50019687, 0.56044219 ],
		[ 0.38710391, 0.72160547 ],
		[ 0.61507734, 0.72034453 ]
	]),
	'dfl_whole_face': numpy.array(
	[
		[ 0.35342266, 0.39285716 ],
		[ 0.62797622, 0.39285716 ],
		[ 0.48660713, 0.54017860 ],
		[ 0.38839287, 0.68750011 ],
		[ 0.59821427, 0.68750011 ]
	]),
	'ffhq_512': numpy.array(
	[
		[ 0.37691676, 0.46864664 ],
		[ 0.62285697, 0.46912813 ],
		[ 0.50123859, 0.61331904 ],
		[ 0.39308822, 0.72541100 ],
		[ 0.61150205, 0.72490465 ]
	]),
	'mtcnn_512': numpy.array(
	[
		[ 0.36562865, 0.46733799 ],
		[ 0.63305391, 0.46585885 ],
		[ 0.50019127, 0.61942959 ],
		[ 0.39032951, 0.77598822 ],
		[ 0.61178945, 0.77476328 ]
	]),
	'styleganex_384': numpy.array(
	[
		[ 0.42353745, 0.52289879 ],
		[ 0.57725008, 0.52319972 ],
		[ 0.50123859, 0.61331904 ],
		[ 0.43364461, 0.68337652 ],
		[ 0.57015325, 0.68306005 ]
	])
}


def estimate_matrix_by_face_landmark_5(face_landmark_5 : FaceLandmark5, warp_template : WarpTemplate, crop_size : Size) -> Matrix:
	normed_warp_template = WARP_TEMPLATE_SET.get(warp_template) * crop_size
	affine_matrix = cv2.estimateAffinePartial2D(face_landmark_5, normed_warp_template, method = cv2.RANSAC, ransacReprojThreshold = 100)[0]
	return affine_matrix


def warp_face_by_face_landmark_5(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5, warp_template : WarpTemplate, crop_size : Size) -> Tuple[VisionFrame, Matrix]:
	affine_matrix = estimate_matrix_by_face_landmark_5(face_landmark_5, warp_template, crop_size)
	crop_vision_frame = cv2.warpAffine(temp_vision_frame, affine_matrix, crop_size, borderMode = cv2.BORDER_REPLICATE, flags = cv2.INTER_AREA)
	return crop_vision_frame, affine_matrix


def warp_face_by_bounding_box(temp_vision_frame : VisionFrame, bounding_box : BoundingBox, crop_size : Size) -> Tuple[VisionFrame, Matrix]:
	source_points = numpy.array([ [ bounding_box[0], bounding_box[1] ], [bounding_box[2], bounding_box[1] ], [ bounding_box[0], bounding_box[3] ] ]).astype(numpy.float32)
	target_points = numpy.array([ [ 0, 0 ], [ crop_size[0], 0 ], [ 0, crop_size[1] ] ]).astype(numpy.float32)
	affine_matrix = cv2.getAffineTransform(source_points, target_points)
	if bounding_box[2] - bounding_box[0] > crop_size[0] or bounding_box[3] - bounding_box[1] > crop_size[1]:
		interpolation_method = cv2.INTER_AREA
	else:
		interpolation_method = cv2.INTER_LINEAR
	crop_vision_frame = cv2.warpAffine(temp_vision_frame, affine_matrix, crop_size, flags = interpolation_method)
	return crop_vision_frame, affine_matrix


def warp_face_by_translation(temp_vision_frame : VisionFrame, translation : Translation, scale : float, crop_size : Size) -> Tuple[VisionFrame, Matrix]:
	affine_matrix = numpy.array([ [ scale, 0, translation[0] ], [ 0, scale, translation[1] ] ])
	crop_vision_frame = cv2.warpAffine(temp_vision_frame, affine_matrix, crop_size)
	return crop_vision_frame, affine_matrix


def paste_back(temp_vision_frame : VisionFrame, crop_vision_frame : VisionFrame, crop_mask : Mask, affine_matrix : Matrix) -> VisionFrame:
	paste_bounding_box, paste_matrix = calc_paste_area(temp_vision_frame, crop_vision_frame, affine_matrix)
	x_min, y_min, x_max, y_max = paste_bounding_box
	paste_width = x_max - x_min
	paste_height = y_max - y_min
	inverse_mask = cv2.warpAffine(crop_mask, paste_matrix, (paste_width, paste_height)).clip(0, 1)
	inverse_mask = numpy.expand_dims(inverse_mask, axis = -1)
	inverse_vision_frame = cv2.warpAffine(crop_vision_frame, paste_matrix, (paste_width, paste_height), borderMode = cv2.BORDER_REPLICATE)
	temp_vision_frame = temp_vision_frame.copy()
	paste_vision_frame = temp_vision_frame[y_min:y_max, x_min:x_max]
	paste_vision_frame = paste_vision_frame * (1 - inverse_mask) + inverse_vision_frame * inverse_mask
	temp_vision_frame[y_min:y_max, x_min:x_max] = paste_vision_frame.astype(temp_vision_frame.dtype)
	return temp_vision_frame


def calc_paste_area(temp_vision_frame : VisionFrame, crop_vision_frame : VisionFrame, affine_matrix : Matrix) -> Tuple[BoundingBox, Matrix]:
	temp_height, temp_width = temp_vision_frame.shape[:2]
	crop_height, crop_width = crop_vision_frame.shape[:2]
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	crop_points = numpy.array([ [ 0, 0 ], [ crop_width, 0 ], [ crop_width, crop_height ], [ 0, crop_height ] ])
	paste_region_points = transform_points(crop_points, inverse_matrix)
	min_point = numpy.floor(paste_region_points.min(axis = 0)).astype(int)
	max_point = numpy.ceil(paste_region_points.max(axis = 0)).astype(int)
	x_min, y_min = numpy.clip(min_point, 0, [ temp_width, temp_height ])
	x_max, y_max = numpy.clip(max_point, 0, [ temp_width, temp_height ])
	paste_bounding_box = numpy.array([ x_min, y_min, x_max, y_max ])
	paste_matrix = inverse_matrix.copy()
	paste_matrix[0, 2] -= x_min
	paste_matrix[1, 2] -= y_min
	return paste_bounding_box, paste_matrix


@lru_cache(maxsize = None)
def create_static_anchors(feature_stride : int, anchor_total : int, stride_height : int, stride_width : int) -> Anchors:
	y, x = numpy.mgrid[:stride_height, :stride_width][::-1]
	anchors = numpy.stack((y, x), axis = -1)
	anchors = (anchors * feature_stride).reshape((-1, 2))
	anchors = numpy.stack([ anchors ] * anchor_total, axis = 1).reshape((-1, 2))
	return anchors


def create_rotated_matrix_and_size(angle : Angle, size : Size) -> Tuple[Matrix, Size]:
	rotated_matrix = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1)
	rotated_size = numpy.dot(numpy.abs(rotated_matrix[:, :2]), size)
	rotated_matrix[:, -1] += (rotated_size - size) * 0.5 #type:ignore[misc]
	rotated_size = int(rotated_size[0]), int(rotated_size[1])
	return rotated_matrix, rotated_size


def create_bounding_box(face_landmark_68 : FaceLandmark68) -> BoundingBox:
	min_x, min_y = numpy.min(face_landmark_68, axis = 0)
	max_x, max_y = numpy.max(face_landmark_68, axis = 0)
	bounding_box = normalize_bounding_box(numpy.array([ min_x, min_y, max_x, max_y ]))
	return bounding_box


def normalize_bounding_box(bounding_box : BoundingBox) -> BoundingBox:
	x1, y1, x2, y2 = bounding_box
	x1, x2 = sorted([ x1, x2 ])
	y1, y2 = sorted([ y1, y2 ])
	return numpy.array([ x1, y1, x2, y2 ])


def transform_points(points : Points, matrix : Matrix) -> Points:
	points = points.reshape(-1, 1, 2)
	points = cv2.transform(points, matrix) #type:ignore[assignment]
	points = points.reshape(-1, 2)
	return points


def transform_bounding_box(bounding_box : BoundingBox, matrix : Matrix) -> BoundingBox:
	points = numpy.array(
	[
		[ bounding_box[0], bounding_box[1] ],
		[ bounding_box[2], bounding_box[1] ],
		[ bounding_box[2], bounding_box[3] ],
		[ bounding_box[0], bounding_box[3] ]
	])
	points = transform_points(points, matrix)
	x1, y1 = numpy.min(points, axis = 0)
	x2, y2 = numpy.max(points, axis = 0)
	return normalize_bounding_box(numpy.array([ x1, y1, x2, y2 ]))


def distance_to_bounding_box(points : Points, distance : Distance) -> BoundingBox:
	x1 = points[:, 0] - distance[:, 0]
	y1 = points[:, 1] - distance[:, 1]
	x2 = points[:, 0] + distance[:, 2]
	y2 = points[:, 1] + distance[:, 3]
	bounding_box = numpy.column_stack([ x1, y1, x2, y2 ])
	return bounding_box


def distance_to_face_landmark_5(points : Points, distance : Distance) -> FaceLandmark5:
	x = points[:, 0::2] + distance[:, 0::2]
	y = points[:, 1::2] + distance[:, 1::2]
	face_landmark_5 = numpy.stack((x, y), axis = -1)
	return face_landmark_5


def scale_face_landmark_5(face_landmark_5 : FaceLandmark5, scale : Scale) -> FaceLandmark5:
	face_landmark_5_scale = face_landmark_5 - face_landmark_5[2]
	face_landmark_5_scale *= scale
	face_landmark_5_scale += face_landmark_5[2]
	return face_landmark_5_scale


def convert_to_face_landmark_5(face_landmark_68 : FaceLandmark68) -> FaceLandmark5:
	face_landmark_5 = numpy.array(
	[
		numpy.mean(face_landmark_68[36:42], axis = 0),
		numpy.mean(face_landmark_68[42:48], axis = 0),
		face_landmark_68[30],
		face_landmark_68[48],
		face_landmark_68[54]
	])
	return face_landmark_5


def estimate_face_angle(face_landmark_68 : FaceLandmark68) -> Angle:
	x1, y1 = face_landmark_68[0]
	x2, y2 = face_landmark_68[16]
	theta = numpy.arctan2(y2 - y1, x2 - x1)
	theta = numpy.degrees(theta) % 360
	angles = numpy.linspace(0, 360, 5)
	index = numpy.argmin(numpy.abs(angles - theta))
	face_angle = int(angles[index] % 360)
	return face_angle


def apply_nms(bounding_boxes : List[BoundingBox], scores : List[Score], score_threshold : float, nms_threshold : float) -> Sequence[int]:
	normed_bounding_boxes = [ (x1, y1, x2 - x1, y2 - y1) for (x1, y1, x2, y2) in bounding_boxes ]
	keep_indices = cv2.dnn.NMSBoxes(normed_bounding_boxes, scores, score_threshold = score_threshold, nms_threshold = nms_threshold)
	return keep_indices


def get_nms_threshold(face_detector_model : FaceDetectorModel, face_detector_angles : List[Angle]) -> float:
	if face_detector_model == 'many':
		return 0.1
	if len(face_detector_angles) == 2:
		return 0.3
	if len(face_detector_angles) == 3:
		return 0.2
	if len(face_detector_angles) == 4:
		return 0.1
	return 0.4


def merge_matrix(matrices : List[Matrix]) -> Matrix:
	merged_matrix = numpy.vstack([ matrices[0], [ 0, 0, 1 ] ])
	for matrix in matrices[1:]:
		matrix = numpy.vstack([ matrix, [ 0, 0, 1 ] ])
		merged_matrix = numpy.dot(merged_matrix, matrix)
	return merged_matrix[:2, :]
