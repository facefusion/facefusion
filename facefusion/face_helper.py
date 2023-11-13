from typing import Any, Dict, Tuple
from functools import lru_cache
from cv2.typing import Size
import cv2
import numpy

from facefusion.typing import Bbox, Kps, Frame, Matrix, Template

TEMPLATES : Dict[Template, numpy.ndarray[Any, Any]] =\
{
	'arcface_v1': numpy.array(
	[
		[ 39.7300, 51.1380 ],
		[ 72.2700, 51.1380 ],
		[ 56.0000, 68.4930 ],
		[ 42.4630, 87.0100 ],
		[ 69.5370, 87.0100 ]
	]),
	'arcface_v2': numpy.array(
	[
		[ 38.2946, 51.6963 ],
		[ 73.5318, 51.5014 ],
		[ 56.0252, 71.7366 ],
		[ 41.5493, 92.3655 ],
		[ 70.7299, 92.2041 ]
	]),
	'ffhq': numpy.array(
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
	affine_matrix = cv2.estimateAffinePartial2D(kps, normed_template, method = cv2.LMEDS)[0]
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (size[1], size[1]), borderMode = cv2.BORDER_REPLICATE)
	return crop_frame, affine_matrix


def paste_back(temp_frame : Frame, crop_frame : Frame, affine_matrix : Matrix) -> Frame:
	inverse_affine_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_frame_height, temp_frame_width = temp_frame.shape[0:2]
	crop_frame_height, crop_frame_width = crop_frame.shape[0:2]
	inverse_mask = numpy.full((crop_frame_height, crop_frame_width), 255).astype(numpy.float32)
	inverse_crop_frame = cv2.warpAffine(inverse_mask, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_temp_frame = cv2.warpAffine(crop_frame, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_mask_size = int(numpy.sqrt(numpy.sum(inverse_crop_frame == 255)))
	kernel_size = max(inverse_mask_size // 10, 10)
	inverse_crop_frame = cv2.erode(inverse_crop_frame, numpy.ones((kernel_size, kernel_size)))
	kernel_size = max(inverse_mask_size // 20, 5)
	blur_size = kernel_size * 2 + 1
	inverse_blur_frame = cv2.GaussianBlur(inverse_crop_frame, (blur_size , blur_size), 0) / 255
	inverse_blur_frame = numpy.reshape(inverse_blur_frame, [ temp_frame_height, temp_frame_width, 1 ])
	temp_frame = inverse_blur_frame * inverse_temp_frame + (1 - inverse_blur_frame) * temp_frame
	temp_frame = temp_frame.astype(numpy.uint8)
	return temp_frame


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
