from typing import Dict, List, Literal, TypeAlias, TypedDict

from facefusion.types import Mask, VisionFrame

FaceSwapperInputs = TypedDict('FaceSwapperInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FaceSwapperModel = Literal['blendswap_256', 'ghost_1_256', 'ghost_2_256', 'ghost_3_256', 'hififace_unofficial_256', 'hyperswap_1a_256', 'hyperswap_1b_256', 'hyperswap_1c_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_unofficial_512', 'uniface_256']

FaceSwapperWeight : TypeAlias = float

FaceSwapperSet : TypeAlias = Dict[FaceSwapperModel, List[str]]
