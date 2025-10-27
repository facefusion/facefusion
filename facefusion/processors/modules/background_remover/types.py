from typing import Literal, TypedDict

from facefusion.types import Mask, VisionFrame

BackgroundRemoverInputs = TypedDict('BackgroundRemoverInputs',
{
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

BackgroundRemoverModel = Literal['ben_2', 'birefnet_general', 'birefnet_portrait', 'birefnet_swin_tiny', 'isnet_general', 'modnet', 'rmbg_1.4', 'rmbg_2.0', 'silueta', 'u2net_general', 'u2net_human_seg', 'u2netp']
