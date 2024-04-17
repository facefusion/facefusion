from typing import Any, Tuple, List
from functools import lru_cache
import cv2
from cv2.typing import Size
import numpy

from facefusion.typing import BoundingBox, FaceLandmark5, FaceLandmark68, VisionFrame, Mask, Matrix, Translation, WarpTemplate, WarpTemplateSet, FaceAnalyserAge, FaceAnalyserGender

WARP_TEMPLATES : WarpTemplateSet =\
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
	'arcface_128_v2': numpy.array(
	[
		[ 0.36167656, 0.40387734 ],
		[ 0.63696719, 0.40235469 ],
		[ 0.50019687, 0.56044219 ],
		[ 0.38710391, 0.72160547 ],
		[ 0.61507734, 0.72034453 ]
	]),
	'ffhq_512': numpy.array(
	[
		[ 0.37691676, 0.46864664 ],
		[ 0.62285697, 0.46912813 ],
		[ 0.50123859, 0.61331904 ],
		[ 0.39308822, 0.72541100 ],
		[ 0.61150205, 0.72490465 ]
	])
}


def estimate_matrix_by_face_landmark_5(face_landmark_5 : FaceLandmark5, warp_template : WarpTemplate, crop_size : Size) -> Matrix:
	normed_warp_template = WARP_TEMPLATES.get(warp_template) * crop_size
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
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_size = temp_vision_frame.shape[:2][::-1]
	inverse_mask = cv2.warpAffine(crop_mask, inverse_matrix, temp_size).clip(0, 1)
	inverse_vision_frame = cv2.warpAffine(crop_vision_frame, inverse_matrix, temp_size, borderMode = cv2.BORDER_REPLICATE)
	paste_vision_frame = temp_vision_frame.copy()
	paste_vision_frame[:, :, 0] = inverse_mask * inverse_vision_frame[:, :, 0] + (1 - inverse_mask) * temp_vision_frame[:, :, 0]
	paste_vision_frame[:, :, 1] = inverse_mask * inverse_vision_frame[:, :, 1] + (1 - inverse_mask) * temp_vision_frame[:, :, 1]
	paste_vision_frame[:, :, 2] = inverse_mask * inverse_vision_frame[:, :, 2] + (1 - inverse_mask) * temp_vision_frame[:, :, 2]
	return paste_vision_frame


@lru_cache(maxsize = None)
def create_static_anchors(feature_stride : int, anchor_total : int, stride_height : int, stride_width : int) -> numpy.ndarray[Any, Any]:
	y, x = numpy.mgrid[:stride_height, :stride_width][::-1]
	anchors = numpy.stack((y, x), axis = -1)
	anchors = (anchors * feature_stride).reshape((-1, 2))
	anchors = numpy.stack([ anchors ] * anchor_total, axis = 1).reshape((-1, 2))
	return anchors


def create_bounding_box_from_face_landmark_68(face_landmark_68 : FaceLandmark68) -> BoundingBox:
	min_x, min_y = numpy.min(face_landmark_68, axis = 0)
	max_x, max_y = numpy.max(face_landmark_68, axis = 0)
	bounding_box = numpy.array([ min_x, min_y, max_x, max_y ]).astype(numpy.int16)
	return bounding_box


def distance_to_bounding_box(points : numpy.ndarray[Any, Any], distance : numpy.ndarray[Any, Any]) -> BoundingBox:
	x1 = points[:, 0] - distance[:, 0]
	y1 = points[:, 1] - distance[:, 1]
	x2 = points[:, 0] + distance[:, 2]
	y2 = points[:, 1] + distance[:, 3]
	bounding_box = numpy.column_stack([ x1, y1, x2, y2 ])
	return bounding_box


def distance_to_face_landmark_5(points : numpy.ndarray[Any, Any], distance : numpy.ndarray[Any, Any]) -> FaceLandmark5:
	x = points[:, 0::2] + distance[:, 0::2]
	y = points[:, 1::2] + distance[:, 1::2]
	face_landmark_5 = numpy.stack((x, y), axis = -1)
	return face_landmark_5


def convert_face_landmark_68_to_5(face_landmark_68 : FaceLandmark68) -> FaceLandmark5:
	face_landmark_5 = numpy.array(
	[
		numpy.mean(face_landmark_68[36:42], axis = 0),
		numpy.mean(face_landmark_68[42:48], axis = 0),
		face_landmark_68[30],
		face_landmark_68[48],
		face_landmark_68[54]
	])
	return face_landmark_5


def apply_nms(bounding_box_list : List[BoundingBox], iou_threshold : float) -> List[int]:
	keep_indices = []
	dimension_list = numpy.reshape(bounding_box_list, (-1, 4))
	x1 = dimension_list[:, 0]
	y1 = dimension_list[:, 1]
	x2 = dimension_list[:, 2]
	y2 = dimension_list[:, 3]
	areas = (x2 - x1 + 1) * (y2 - y1 + 1)
	indices = numpy.arange(len(bounding_box_list))
	while indices.size > 0:
		index = indices[0]
		remain_indices = indices[1:]
		keep_indices.append(index)
		xx1 = numpy.maximum(x1[index], x1[remain_indices])
		yy1 = numpy.maximum(y1[index], y1[remain_indices])
		xx2 = numpy.minimum(x2[index], x2[remain_indices])
		yy2 = numpy.minimum(y2[index], y2[remain_indices])
		width = numpy.maximum(0, xx2 - xx1 + 1)
		height = numpy.maximum(0, yy2 - yy1 + 1)
		iou = width * height / (areas[index] + areas[remain_indices] - width * height)
		indices = indices[numpy.where(iou <= iou_threshold)[0] + 1]
	return keep_indices


def categorize_age(age : int) -> FaceAnalyserAge:
	if age < 13:
		return 'child'
	elif age < 19:
		return 'teen'
	elif age < 60:
		return 'adult'
	return 'senior'


def categorize_gender(gender : int) -> FaceAnalyserGender:
	if gender == 0:
		return 'female'
	return 'male'
