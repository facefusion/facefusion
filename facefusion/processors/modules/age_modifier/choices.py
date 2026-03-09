from typing import List, Sequence, get_args

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.age_modifier.types import AgeModifierModel

age_modifier_models : List[AgeModifierModel] = list(get_args(AgeModifierModel))

age_modifier_direction_range : Sequence[int] = create_int_range(-100, 100, 1)
