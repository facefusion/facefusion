from typing import Any, List, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import Mask, VisionFrame

DeepSwapperInputs = TypedDict('DeepSwapperInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frames' : List[VisionFrame],
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

DeepSwapperModel : TypeAlias = str

DeepSwapperMorph : TypeAlias = NDArray[Any]
