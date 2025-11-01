from typing import Any, Literal, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import Mask, VisionFrame

FaceEnhancerInputs = TypedDict('FaceEnhancerInputs',
{
	'reference_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FaceEnhancerModel = Literal['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'gpen_bfr_1024', 'gpen_bfr_2048', 'restoreformer_plus_plus']

FaceEnhancerWeight : TypeAlias = NDArray[Any]
