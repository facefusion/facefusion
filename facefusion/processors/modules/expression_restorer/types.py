from typing import List, Literal, TypedDict

from facefusion.types import Mask, VisionFrame

ExpressionRestorerInputs = TypedDict('ExpressionRestorerInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

ExpressionRestorerModel = Literal['live_portrait']

ExpressionRestorerArea = Literal['upper-face', 'lower-face']
