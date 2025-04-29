from typing import List

import numpy
from cv2.typing import Size

from facefusion.types import VisionFrame


def implode_pixel_boost(crop_vision_frame : VisionFrame, pixel_boost_total : int, model_size : Size) -> VisionFrame:
	pixel_boost_vision_frame = crop_vision_frame.reshape(model_size[0], pixel_boost_total, model_size[1], pixel_boost_total, 3)
	pixel_boost_vision_frame = pixel_boost_vision_frame.transpose(1, 3, 0, 2, 4).reshape(pixel_boost_total ** 2, model_size[0], model_size[1], 3)
	return pixel_boost_vision_frame


def explode_pixel_boost(temp_vision_frames : List[VisionFrame], pixel_boost_total : int, model_size : Size, pixel_boost_size : Size) -> VisionFrame:
	crop_vision_frame = numpy.stack(temp_vision_frames).reshape(pixel_boost_total, pixel_boost_total, model_size[0], model_size[1], 3)
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 3, 1, 4).reshape(pixel_boost_size[0], pixel_boost_size[1], 3)
	return crop_vision_frame
