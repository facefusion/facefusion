from typing import List, Sequence

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.processors.typing import AgeModifierModel, ExpressionRestorerModel, FaceDebuggerItem, FaceEditorModel, FaceEnhancerModel, FaceSwapperSet, FrameColorizerModel, FrameEnhancerModel, LipSyncerModel

age_modifier_models : List[AgeModifierModel] = [ 'styleganex_age' ]
expression_restorer_models : List[ExpressionRestorerModel] = [ 'live_portrait' ]
face_debugger_items : List[FaceDebuggerItem] = [ 'bounding-box', 'face-landmark-5', 'face-landmark-5/68', 'face-landmark-68', 'face-landmark-68/5', 'face-mask', 'face-detector-score', 'face-landmarker-score', 'age', 'gender', 'race' ]
face_editor_models : List[FaceEditorModel] = [ 'live_portrait' ]
face_enhancer_models : List[FaceEnhancerModel] = [ 'codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'gpen_bfr_1024', 'gpen_bfr_2048', 'restoreformer_plus_plus' ]
face_swapper_set : FaceSwapperSet =\
{
	'blendswap_256': [ '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'ghost_1_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'ghost_2_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'ghost_3_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'inswapper_128': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'inswapper_128_fp16': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'simswap_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'simswap_unofficial_512': [ '512x512', '768x768', '1024x1024' ],
	'uniface_256': [ '256x256', '512x512', '768x768', '1024x1024' ]
}
frame_colorizer_models : List[FrameColorizerModel] = [ 'ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable' ]
frame_colorizer_sizes : List[str] = [ '192x192', '256x256', '384x384', '512x512' ]
frame_enhancer_models : List[FrameEnhancerModel] = [ 'clear_reality_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_esrgan_x8', 'real_esrgan_x8_fp16', 'real_hatgan_x4', 'span_kendata_x4', 'ultra_sharp_x4' ]
lip_syncer_models : List[LipSyncerModel] = [ 'wav2lip_96', 'wav2lip_gan_96' ]

age_modifier_direction_range : Sequence[int] = create_int_range(-100, 100, 1)
expression_restorer_factor_range : Sequence[int] = create_int_range(0, 100, 1)
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
face_enhancer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
frame_colorizer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
frame_enhancer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
