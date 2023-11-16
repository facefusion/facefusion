from typing import Any, Dict, Tuple
from functools import lru_cache
from cv2.typing import Size
import cv2
import numpy

from facefusion.typing import Bbox, Kps, Frame, Matrix, Template, Padding

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


def paste_back(temp_frame: numpy.ndarray, crop_frame: numpy.ndarray, affine_matrix: numpy.ndarray, blur: float, padding: Padding):
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_frame_size = temp_frame.shape[:2][::-1]
	mask = create_static_mask(tuple(crop_frame.shape[:2]), blur, tuple(padding))
	mask_warped = cv2.warpAffine(mask, inverse_matrix, temp_frame_size).clip(0, 1)
	crop_frame_warped = cv2.warpAffine(crop_frame, inverse_matrix, temp_frame_size, borderMode=cv2.BORDER_REPLICATE)
	composite_frame = temp_frame.copy()
	composite_frame[:, :, 0] = mask_warped * crop_frame_warped[:, :, 0] + (1 - mask_warped) * temp_frame[:, :, 0]
	composite_frame[:, :, 1] = mask_warped * crop_frame_warped[:, :, 1] + (1 - mask_warped) * temp_frame[:, :, 1]
	composite_frame[:, :, 2] = mask_warped * crop_frame_warped[:, :, 2] + (1 - mask_warped) * temp_frame[:, :, 2]
	return composite_frame


@lru_cache(maxsize = None)
def create_static_mask(size : Tuple[int, int], blur : float, padding : Padding) -> numpy.ndarray[Any, Any]:
	mask = numpy.ones(size, dtype='float32')
	blur_amount = int(size[0] * 0.5 * blur)
	blur_area = max(blur_amount // 2, 1)
	mask[:max(blur_area, int(padding[0] * size[1])), :] = 0
	mask[-max(blur_area, int(padding[1] * size[1])):, :] = 0
	mask[:, :max(blur_area, int(padding[2] * size[0]))] = 0
	mask[:, -max(blur_area, int(padding[3] * size[0])):] = 0
	if blur_amount > 0:
		mask = cv2.GaussianBlur(mask, (0, 0), blur_amount * 0.25)
	return mask


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
