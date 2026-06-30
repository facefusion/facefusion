from typing import List, Literal, TypedDict

from facefusion.types import Mask, VisionFrame

FaceEditorInputs = TypedDict('FaceEditorInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frames' : List[VisionFrame],
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FaceEditorModel = Literal['live_portrait']
