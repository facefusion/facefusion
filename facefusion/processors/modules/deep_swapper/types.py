from typing import Any, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import VisionFrame

DeepSwapperInputs = TypedDict('DeepSwapperInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame
})

DeepSwapperModel : TypeAlias = str

DeepSwapperMorph : TypeAlias = NDArray[Any]
