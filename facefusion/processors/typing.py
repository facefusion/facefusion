from typing import Any, Dict, List, Literal, TypedDict

from numpy._typing import NDArray

from facefusion.typing import AppContext, AudioFrame, Face, FaceSet, VisionFrame

AgeModifierModel = Literal['styleganex_age']
DeepSwapperModel = Literal\
[
	'iperov/emma_watson_224',
	'iperov/keanu_reeves_320',
	'iperov/jackie_chan_224',
	'iperov/alexandra_daddario_224',
	'iperov/alexei_navalny_224',
	'iperov/amber_heard_224',
	'iperov/dilraba_dilmurat_224',
	'iperov/elon_musk_224',
	'iperov/emilia_clarke_224',
	'iperov/emma_watson_224',
	'iperov/erin_moriarty_224',
	'iperov/jackie_chan_224',
	'iperov/james_carrey_224',
	'iperov/jason_statham_320',
	'iperov/jessica_alba_224',
	'iperov/keanu_reeves_320',
	'iperov/lucy_liu_224',
	'iperov/margot_robbie_224',
	'iperov/meghan_markle_224',
	'iperov/natalie_dormer_224',
	'iperov/natalie_portman_224',
	'iperov/nicolas_coppola__224',
	'iperov/robert_downey_224',
	'iperov/rowan_atkinson_224',
	'iperov/ryan_reynolds_224',
	'iperov/scarlett_johansson_224',
	'iperov/sylvester_stallone_224',
	'iperov/taylor_swift_224',
	'iperov/thomas_cruise_224',
	'iperov/thomas_holland_224',
	'iperov/vin_diesel_224',
	'iperov/vladimir_putin_224',
	'iperov/emma_watson_224',
	'iperov/keanu_reeves_320',
	'iperov/jackie_chan_224',
	'iperov/alexandra_daddario_224',
	'iperov/alexei_navalny_224',
	'iperov/amber_heard_224',
	'iperov/dilraba_dilmurat_224',
	'iperov/elon_musk_224',
	'iperov/emilia_clarke_224',
	'iperov/emma_watson_224',
	'iperov/erin_moriarty_224',
	'iperov/jackie_chan_224',
	'iperov/james_carrey_224',
	'iperov/jason_statham_320',
	'iperov/jessica_alba_224',
	'iperov/keanu_reeves_320',
	'iperov/lucy_liu_224',
	'iperov/margot_robbie_224',
	'iperov/meghan_markle_224',
	'iperov/natalie_dormer_224',
	'iperov/natalie_portman_224',
	'iperov/nicolas_coppola__224',
	'iperov/robert_downey_224',
	'iperov/rowan_atkinson_224',
	'iperov/ryan_reynolds_224',
	'iperov/scarlett_johansson_224',
	'iperov/sylvester_stallone_224',
	'iperov/taylor_swift_224',
	'iperov/thomas_cruise_224',
	'iperov/thomas_holland_224',
	'iperov/vin_diesel_224',
	'iperov/vladimir_putin_224'
]
ExpressionRestorerModel = Literal['live_portrait']
FaceDebuggerItem = Literal['bounding-box', 'face-landmark-5', 'face-landmark-5/68', 'face-landmark-68', 'face-landmark-68/5', 'face-mask', 'face-detector-score', 'face-landmarker-score', 'age', 'gender', 'race']
FaceEditorModel = Literal['live_portrait']
FaceEnhancerModel = Literal['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'gpen_bfr_1024', 'gpen_bfr_2048', 'restoreformer_plus_plus']
FaceSwapperModel = Literal['blendswap_256', 'ghost_1_256', 'ghost_2_256', 'ghost_3_256', 'hififace_unofficial_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_unofficial_512', 'uniface_256']
FrameColorizerModel = Literal['ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable']
FrameEnhancerModel = Literal['clear_reality_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_esrgan_x8', 'real_esrgan_x8_fp16', 'real_hatgan_x4', 'real_web_photo_x4', 'realistic_rescaler_x4', 'remacri_x4', 'siax_x4', 'span_kendata_x4', 'swin2_sr_x4', 'ultra_sharp_x4']
LipSyncerModel = Literal['wav2lip_96', 'wav2lip_gan_96']

FaceSwapperSet = Dict[FaceSwapperModel, List[str]]

AgeModifierInputs = TypedDict('AgeModifierInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})
DeepSwapperInputs = TypedDict('DeepSwapperInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})
ExpressionRestorerInputs = TypedDict('ExpressionRestorerInputs',
{
	'reference_faces' : FaceSet,
	'source_vision_frame' : VisionFrame,
	'target_vision_frame' : VisionFrame
})
FaceDebuggerInputs = TypedDict('FaceDebuggerInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})
FaceEditorInputs = TypedDict('FaceEditorInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})
FaceEnhancerInputs = TypedDict('FaceEnhancerInputs',
{
	'reference_faces' : FaceSet,
	'target_vision_frame' : VisionFrame
})
FaceSwapperInputs = TypedDict('FaceSwapperInputs',
{
	'reference_faces' : FaceSet,
	'source_face' : Face,
	'target_vision_frame' : VisionFrame
})
FrameColorizerInputs = TypedDict('FrameColorizerInputs',
{
	'target_vision_frame' : VisionFrame
})
FrameEnhancerInputs = TypedDict('FrameEnhancerInputs',
{
	'target_vision_frame' : VisionFrame
})
LipSyncerInputs = TypedDict('LipSyncerInputs',
{
	'reference_faces' : FaceSet,
	'source_audio_frame' : AudioFrame,
	'target_vision_frame' : VisionFrame
})

ProcessorStateKey = Literal\
[
	'age_modifier_model',
	'age_modifier_direction',
	'deep_swapper_model',
	'expression_restorer_model',
	'expression_restorer_factor',
	'face_debugger_items',
	'face_editor_model',
	'face_editor_eyebrow_direction',
	'face_editor_eye_gaze_horizontal',
	'face_editor_eye_gaze_vertical',
	'face_editor_eye_open_ratio',
	'face_editor_lip_open_ratio',
	'face_editor_mouth_grim',
	'face_editor_mouth_pout',
	'face_editor_mouth_purse',
	'face_editor_mouth_smile',
	'face_editor_mouth_position_horizontal',
	'face_editor_mouth_position_vertical',
	'face_editor_head_pitch',
	'face_editor_head_yaw',
	'face_editor_head_roll',
	'face_enhancer_model',
	'face_enhancer_blend',
	'face_swapper_model',
	'face_swapper_pixel_boost',
	'frame_colorizer_model',
	'frame_colorizer_size',
	'frame_colorizer_blend',
	'frame_enhancer_model',
	'frame_enhancer_blend',
	'lip_syncer_model'
]
ProcessorState = TypedDict('ProcessorState',
{
	'age_modifier_model' : AgeModifierModel,
	'age_modifier_direction' : int,
	'deep_swapper_model' : DeepSwapperModel,
	'expression_restorer_model' : ExpressionRestorerModel,
	'expression_restorer_factor' : int,
	'face_debugger_items' : List[FaceDebuggerItem],
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
	'face_editor_head_roll' : float,
	'face_enhancer_model' : FaceEnhancerModel,
	'face_enhancer_blend' : int,
	'face_swapper_model' : FaceSwapperModel,
	'face_swapper_pixel_boost' : str,
	'frame_colorizer_model' : FrameColorizerModel,
	'frame_colorizer_size' : str,
	'frame_colorizer_blend' : int,
	'frame_enhancer_model' : FrameEnhancerModel,
	'frame_enhancer_blend' : int,
	'lip_syncer_model' : LipSyncerModel
})
ProcessorStateSet = Dict[AppContext, ProcessorState]

LivePortraitPitch = float
LivePortraitYaw = float
LivePortraitRoll = float
LivePortraitExpression = NDArray[Any]
LivePortraitFeatureVolume = NDArray[Any]
LivePortraitMotionPoints = NDArray[Any]
LivePortraitRotation = NDArray[Any]
LivePortraitScale = NDArray[Any]
LivePortraitTranslation = NDArray[Any]
