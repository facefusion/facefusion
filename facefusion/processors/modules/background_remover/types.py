from typing import Literal, TypedDict

from facefusion.types import Mask, VisionFrame

BackgroundRemoverInputs = TypedDict('BackgroundRemoverInputs',
{
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

BackgroundRemoverModel = Literal['ben_2', 'birefnet_general', 'birefnet_portrait', 'isnet_general', 'modnet', 'ormbg', 'rmbg_1.4', 'rmbg_2.0', 'silueta', 'u2net_cloth', 'u2net_general', 'u2net_human', 'u2netp']
