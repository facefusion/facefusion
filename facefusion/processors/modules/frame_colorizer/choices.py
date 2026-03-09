from typing import List, Sequence, get_args

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.frame_colorizer.types import FrameColorizerModel

frame_colorizer_models : List[FrameColorizerModel] = list(get_args(FrameColorizerModel))

frame_colorizer_sizes : List[str] = [ '192x192', '256x256', '384x384', '512x512' ]

frame_colorizer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
