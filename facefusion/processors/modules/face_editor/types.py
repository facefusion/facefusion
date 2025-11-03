from typing import Literal, TypedDict

from facefusion.types import Mask, VisionFrame

FaceEditorInputs = TypedDict('FaceEditorInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FaceEditorModel = Literal['live_portrait']
