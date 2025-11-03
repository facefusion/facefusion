from typing import List, Sequence

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.background_remover.types import BackgroundRemoverModel

background_remover_models : List[BackgroundRemoverModel] = [ 'ben_2', 'birefnet_general', 'birefnet_portrait', 'isnet_general', 'modnet', 'ormbg', 'rmbg_1.4', 'rmbg_2.0', 'silueta', 'u2net_cloth', 'u2net_general', 'u2net_human', 'u2netp' ]

background_remover_color_range : Sequence[int] = create_int_range(0, 255, 1)
