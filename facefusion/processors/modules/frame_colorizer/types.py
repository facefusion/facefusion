from typing import List, Literal, TypedDict

from facefusion.types import Mask, VisionFrame

FrameColorizerInputs = TypedDict('FrameColorizerInputs',
{
	'target_vision_frames' : List[VisionFrame],
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FrameColorizerModel = Literal['ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable']

State = TypedDict('State',
{
	'frame_colorizer_model' : FrameColorizerModel,
	'frame_colorizer_size' : str,
	'frame_colorizer_blend' : int
})
