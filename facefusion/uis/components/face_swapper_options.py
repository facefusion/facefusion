from typing import List, Optional, Tuple

import gradio

from facefusion import state_manager, translator
from facefusion.common_helper import calculate_float_step, get_first
from facefusion.processors.modules.face_swapper import choices as face_swapper_choices
from facefusion.processors.modules.face_swapper.locals import LOCALS
from facefusion.processors.core import load_processor_module
from facefusion.processors.modules.face_swapper.types import FaceSwapperModel, FaceSwapperWeight
from facefusion.uis.core import get_ui_component, register_ui_component


translator.load(LOCALS, __name__)

FACE_SWAPPER_MODEL_DROPDOWN : Optional[gradio.Dropdown] = None