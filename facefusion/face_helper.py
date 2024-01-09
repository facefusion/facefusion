from typing import Any, Dict, Tuple, List
from cv2.typing import Size
from functools import lru_cache
import cv2
import numpy

from facefusion.typing import Bbox, Kps, Frame, Mask, Matrix, Template

TEMPLATES : Dict[Template, numpy.ndarray[Any, Any]] =\
{
	'arcface_112_v1': numpy.array(
	[
		[0.35473214, 0.45658929],
		[0.64526786, 0.45658929],
		[0.50000000, 0.61154464],
		[0.37913393, 0.77687500],
		[0.62086607, 0.77687500]
	]),
	'arcface_112_v2': numpy.array(
	[
		[0.34191607, 0.46157411],
		[0.65653393, 0.45983393],
		[0.50022500, 0.64050536],
		[0.37097589, 0.82469196],
		[0.63151696, 0.82325089]
	]),
	'arcface_128_v2': numpy.array(
	[
		[0.36167656, 0.40387734],
		[0.63696719, 0.40235469],
		[0.50019687, 0.56044219],
		[0.38710391, 0.72160547],
		[0.61507734, 0.72034453]
	]),
	'ffhq_512': numpy.array(
	[
		[0.37691676, 0.46864664],
		[0.62285697, 0.46912813],
		[0.50123859, 0.61331904],
		[0.39308822, 0.72541100],
		[0.61150205, 0.72490465]
	])
}


def warp_face_by_kps(temp_frame : Frame, kps : Kps, template : Template, size : Size) -> Tuple[Frame, Matrix]:
	normed_template = TEMPLATES.get(template) * size
	affine_matrix = cv2.estimateAffinePartial2D(kps, normed_template, method = cv2.RANSAC, ransacReprojThreshold = 100)[0]
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (size[0], size[1]), borderMode = cv2.BORDER_REPLICATE, flags = cv2.INTER_AREA)
	return crop_frame, affine_matrix


def warp_face_by_bbox(temp_frame : Frame, bbox : Bbox, size : Size) -> Tuple[Frame, Matrix]:
	source_points = numpy.float32([[bbox[0], bbox[1]], [bbox[2], bbox[1]], [bbox[0], bbox[3]]])
	target_points = numpy.float32([[0, 0], [size[0], 0], [0, size[1]]])
	affine_matrix = cv2.getAffineTransform(source_points, target_points)
	bbox_width, bbox_height = bbox[2] - bbox[0], bbox[2] - bbox[1]
	interpolation_method = cv2.INTER_AREA if max(bbox_width, bbox_height) > max(*size) else cv2.INTER_LINEAR
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, size, borderValue=0.0, flags = interpolation_method)
	return crop_frame, affine_matrix


def paste_back(temp_frame : Frame, crop_frame : Frame, crop_mask : Mask, affine_matrix : Matrix) -> Frame:
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_frame_size = temp_frame.shape[:2][::-1]
	inverse_crop_mask = cv2.warpAffine(crop_mask, inverse_matrix, temp_frame_size).clip(0, 1)
	inverse_crop_frame = cv2.warpAffine(crop_frame, inverse_matrix, temp_frame_size, borderMode = cv2.BORDER_REPLICATE)
	paste_frame = temp_frame.copy()
	paste_frame[:, :, 0] = inverse_crop_mask * inverse_crop_frame[:, :, 0] + (1 - inverse_crop_mask) * temp_frame[:, :, 0]
	paste_frame[:, :, 1] = inverse_crop_mask * inverse_crop_frame[:, :, 1] + (1 - inverse_crop_mask) * temp_frame[:, :, 1]
	paste_frame[:, :, 2] = inverse_crop_mask * inverse_crop_frame[:, :, 2] + (1 - inverse_crop_mask) * temp_frame[:, :, 2]
	return paste_frame


@lru_cache(maxsize = None)
def create_static_anchors(feature_stride : int, anchor_total : int, stride_height : int, stride_width : int) -> numpy.ndarray[Any, Any]:
	y, x = numpy.mgrid[:stride_height, :stride_width][::-1]
	anchors = numpy.stack((y, x), axis = -1)
	anchors = (anchors * feature_stride).reshape((-1, 2))
	anchors = numpy.stack([ anchors ] * anchor_total, axis = 1).reshape((-1, 2))
	return anchors


def distance_to_bbox(points : numpy.ndarray[Any, Any], distance : numpy.ndarray[Any, Any]) -> Bbox:
	x1 = points[:, 0] - distance[:, 0]
	y1 = points[:, 1] - distance[:, 1]
	x2 = points[:, 0] + distance[:, 2]
	y2 = points[:, 1] + distance[:, 3]
	bbox = numpy.column_stack([ x1, y1, x2, y2 ])
	return bbox


def distance_to_kps(points : numpy.ndarray[Any, Any], distance : numpy.ndarray[Any, Any]) -> Kps:
	x = points[:, 0::2] + distance[:, 0::2]
	y = points[:, 1::2] + distance[:, 1::2]
	kps = numpy.stack((x, y), axis = -1)
	return kps


def apply_nms(bbox_list : List[Bbox], iou_threshold : float) -> List[int]:
	keep_indices = []
	dimension_list = numpy.reshape(bbox_list, (-1, 4))
	x1 = dimension_list[:, 0]
	y1 = dimension_list[:, 1]
	x2 = dimension_list[:, 2]
	y2 = dimension_list[:, 3]
	areas = (x2 - x1 + 1) * (y2 - y1 + 1)
	indices = numpy.arange(len(bbox_list))
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
