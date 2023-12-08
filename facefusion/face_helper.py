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
		[ 39.7300, 51.1380 ],
		[ 72.2700, 51.1380 ],
		[ 56.0000, 68.4930 ],
		[ 42.4630, 87.0100 ],
		[ 69.5370, 87.0100 ]
	]),
	'arcface_112_v2': numpy.array(
	[
		[ 38.2946, 51.6963 ],
		[ 73.5318, 51.5014 ],
		[ 56.0252, 71.7366 ],
		[ 41.5493, 92.3655 ],
		[ 70.7299, 92.2041 ]
	]),
	'arcface_128_v2': numpy.array(
	[
		[ 46.2946, 51.6963 ],
		[ 81.5318, 51.5014 ],
		[ 64.0252, 71.7366 ],
		[ 49.5493, 92.3655 ],
		[ 78.7299, 92.2041 ]
	]),
	'ffhq_512': numpy.array(
	[
		[ 192.98138, 239.94708 ],
		[ 318.90277, 240.1936 ],
		[ 256.63416, 314.01935 ],
		[ 201.26117, 371.41043 ],
		[ 313.08905, 371.15118 ]
	])
}


def warp_face(temp_frame : Frame, kps : Kps, template : Template, size : Size) -> Tuple[Frame, Matrix]:
	normed_template = TEMPLATES.get(template) * size[1] / size[0]
	affine_matrix = cv2.estimateAffinePartial2D(kps, normed_template, method = cv2.RANSAC, ransacReprojThreshold = 100)[0]
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (size[1], size[1]), borderMode = cv2.BORDER_REPLICATE)
	return crop_frame, affine_matrix


def paste_back(temp_frame : Frame, crop_frame: Frame, crop_mask : Mask, affine_matrix : Matrix) -> Frame:
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
