from typing import Any, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import Mask, VisionFrame

DeepSwapperInputs = TypedDict('DeepSwapperInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

DeepSwapperModel : TypeAlias = str

DeepSwapperMorph : TypeAlias = NDArray[Any]
