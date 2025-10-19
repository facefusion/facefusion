from typing import Literal, TypedDict

from facefusion.types import VisionFrame

BackgroundRemoverInputs = TypedDict('BackgroundRemoverInputs',
{
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame
})

BackgroundRemoverModel = Literal['birefnet_general_244', 'rmbg_1.4', 'rmbg_2.0', 'ben2', 'birefnet_portrait', 'birefnet_swin_tiny', 'isnet_general', 'modnet', 'silueta', 'u2net', 'u2net_human_seg', 'u2netp']
