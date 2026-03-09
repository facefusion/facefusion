from typing import List, Sequence, get_args

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.expression_restorer.types import ExpressionRestorerArea, ExpressionRestorerModel

expression_restorer_models : List[ExpressionRestorerModel] = list(get_args(ExpressionRestorerModel))

expression_restorer_areas : List[ExpressionRestorerArea] = list(get_args(ExpressionRestorerArea))

expression_restorer_factor_range : Sequence[int] = create_int_range(0, 100, 1)
