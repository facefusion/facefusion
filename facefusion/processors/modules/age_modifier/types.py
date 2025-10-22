from typing import Any, Literal, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import Mask, VisionFrame

AgeModifierInputs = TypedDict('AgeModifierInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

AgeModifierModel = Literal['styleganex_age']

AgeModifierDirection : TypeAlias = NDArray[Any]
