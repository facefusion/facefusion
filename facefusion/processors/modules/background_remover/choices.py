from typing import List, Sequence

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.background_remover.types import BackgroundRemoverModel

background_remover_models : List[BackgroundRemoverModel] = [ 'birefnet_general_244', 'rmbg_1.4', 'rmbg_2.0', 'ben2', 'birefnet_portrait', 'birefnet_swin_tiny', 'isnet_general', 'modnet', 'silueta', 'u2net', 'u2net_human_seg', 'u2netp' ]

background_remover_color_range : Sequence[int] = create_int_range(0, 255, 1)
