from typing import Tuple, Dict, Any

import cv2
import numpy
from cv2.typing import Size

from facefusion.typing import Frame, Kps, Matrix, Template

TEMPLATES : Dict[Template, numpy.ndarray[Any, Any]] =\
{
	'arcface': numpy.array(
	[
		[ 38.2946, 51.6963 ],
		[ 73.5318, 51.5014 ],
		[ 56.0252, 71.7366 ],
		[ 41.5493, 92.3655 ],
		[ 70.7299, 92.2041 ]
	]),
	'ghost': numpy.array(
	[
		[
			[ 51.6420, 50.1150 ],
			[ 57.6170, 49.9900 ],
			[ 35.7400, 69.0070 ],
			[ 51.1570, 89.0500 ],
			[ 57.0250, 89.7020 ],
		],
		[
			[ 45.0310, 50.1180 ],
			[ 65.5680, 50.8720 ],
			[ 39.6770, 68.1110 ],
			[ 45.1770, 86.1900 ] ,
			[ 64.2460, 86.7580 ],
		],
		[
			[ 39.7300, 51.1380 ],
			[ 72.2700, 51.1380 ],
			[ 56.0000, 68.4930 ],
			[ 42.4630, 87.0100 ],
			[ 69.5370, 87.0100 ],
		],
		[
			[ 46.8450, 50.8720 ],
			[ 67.3820, 50.1180 ],
			[ 72.7370, 68.1110 ],
			[ 48.1670, 86.7580 ],
			[ 67.2360, 86.1900 ],
		],
		[
			[ 54.7960, 49.9900 ],
			[ 60.7710, 50.1150 ],
			[ 76.6730, 69.0070 ],
			[ 55.3880, 89.7020 ],
			[ 61.2570, 89.0500 ],
		],
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
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (size[1], size[1]))
	return crop_frame, affine_matrix


def paste_back(temp_frame: Frame, crop_frame: Frame, affine_matrix: Matrix) -> Frame:
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
