from typing import List, Sequence

from facefusion.common_helper import create_float_range
from facefusion.processors.modules.face_editor.types import FaceEditorModel

face_editor_models : List[FaceEditorModel] = [ 'live_portrait' ]

face_editor_eyebrow_direction_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_eye_gaze_horizontal_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_eye_gaze_vertical_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_eye_open_ratio_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_lip_open_ratio_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_grim_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_pout_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_purse_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_smile_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_position_horizontal_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_mouth_position_vertical_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_head_pitch_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_head_yaw_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
face_editor_head_roll_range : Sequence[float] = create_float_range(-1.0, 1.0, 0.05)
