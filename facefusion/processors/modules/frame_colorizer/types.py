from typing import Literal, TypedDict

from facefusion.types import Mask, VisionFrame

FrameColorizerInputs = TypedDict('FrameColorizerInputs',
{
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FrameColorizerModel = Literal['ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable']
