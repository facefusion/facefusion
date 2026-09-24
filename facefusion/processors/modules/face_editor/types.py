from typing import List, Literal, TypedDict

from facefusion.types import Mask, VisionFrame

FaceEditorInputs = TypedDict('FaceEditorInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_vision_frames' : List[VisionFrame],
	'target_vision_frames' : List[VisionFrame],
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

FaceEditorModel = Literal['live_portrait']

State = TypedDict('State',
{
	'face_editor_model' : FaceEditorModel,
	'face_editor_eyebrow_direction' : float,
	'face_editor_eye_gaze_horizontal' : float,
	'face_editor_eye_gaze_vertical' : float,
	'face_editor_eye_open_ratio' : float,
	'face_editor_lip_open_ratio' : float,
	'face_editor_mouth_grim' : float,
	'face_editor_mouth_pout' : float,
	'face_editor_mouth_purse' : float,
	'face_editor_mouth_smile' : float,
	'face_editor_mouth_position_horizontal' : float,
	'face_editor_mouth_position_vertical' : float,
	'face_editor_head_pitch' : float,
	'face_editor_head_yaw' : float,
	'face_editor_head_roll' : float
})
