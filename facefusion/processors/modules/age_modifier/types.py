from typing import Any, Literal, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import VisionFrame

AgeModifierInputs = TypedDict('AgeModifierInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame
})

AgeModifierModel = Literal['styleganex_age']

AgeModifierDirection : TypeAlias = NDArray[Any]
