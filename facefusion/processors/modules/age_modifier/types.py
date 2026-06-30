from typing import Any, List, Literal, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import Mask, VisionFrame

AgeModifierInputs = TypedDict('AgeModifierInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frames' : List[VisionFrame],
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

AgeModifierModel = Literal['fran', 'styleganex_age']

AgeModifierDirection : TypeAlias = NDArray[Any]
