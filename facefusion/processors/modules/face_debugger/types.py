from typing import Literal, TypedDict

from facefusion.types import VisionFrame

FaceDebuggerInputs = TypedDict('FaceDebuggerInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame
})

FaceDebuggerItem = Literal['bounding-box', 'face-landmark-5', 'face-landmark-5/68', 'face-landmark-68', 'face-landmark-68/5', 'face-mask']
