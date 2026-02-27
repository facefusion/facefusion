from typing import List, Sequence, get_args

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.processors.modules.face_enhancer.types import FaceEnhancerModel

face_enhancer_models : List[FaceEnhancerModel] = list(get_args(FaceEnhancerModel))

face_enhancer_blend_range : Sequence[int] = create_int_range(0, 100, 1)

face_enhancer_weight_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
