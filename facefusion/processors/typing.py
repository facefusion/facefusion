from typing import Any, Dict, List, Literal, TypedDict

from numpy._typing import NDArray

from facefusion.typing import AppContext, AudioFrame, Face, FaceSet, VisionFrame

AgeModifierModel = Literal['styleganex_age']
DeepSwapperModel = Literal\
[
	'druuzil/adrianne_palicki_384',
	'druuzil/agnetha_falskog_224',
	'druuzil/alan_ritchson_320',
	'druuzil/alicia_vikander_320',
	'druuzil/amber_midthunder_320',
	'druuzil/andras_arato_384',
	'druuzil/andrew_tate_320',
	'druuzil/anne_hathaway_320',
	'druuzil/anya_chalotra_320',
	'druuzil/arnold_schwarzenegger_320',
	'druuzil/benjamin_affleck_320',
	'druuzil/benjamin_stiller_384',
	'druuzil/bradley_pitt_224',
	'druuzil/bryan_cranston_320',
	'druuzil/catherine_blanchett_352',
	'druuzil/christian_bale_320',
	'druuzil/christopher_hemsworth_320',
	'druuzil/christoph_waltz_384',
	'druuzil/cillian_murphy_320',
	'druuzil/cobie_smulders_256',
	'druuzil/dwayne_johnson_384',
	'druuzil/edward_norton_320',
	'druuzil/elisabeth_shue_320',
	'druuzil/elizabeth_olsen_384',
	'druuzil/elon_musk_320',
	'druuzil/emily_blunt_320',
	'druuzil/emma_stone_384',
	'druuzil/emma_watson_320',
	'druuzil/erin_moriarty_384',
	'druuzil/eva_green_320',
	'druuzil/ewan_mcgregor_320',
	'druuzil/florence_pugh_320',
	'druuzil/freya_allan_320',
	'druuzil/gary_cole_224',
	'druuzil/gigi_hadid_224',
	'druuzil/harrison_ford_384',
	'druuzil/hayden_christensen_320',
	'druuzil/heath_ledger_320',
	'druuzil/henry_cavill_448',
	'druuzil/hugh_jackman_384',
	'druuzil/idris_elba_320',
	'druuzil/jack_nicholson_320',
	'druuzil/james_mcavoy_320',
	'druuzil/james_varney_320',
	'druuzil/jason_momoa_320',
	'druuzil/jason_statham_320',
	'druuzil/jennifer_connelly_384',
	'druuzil/jimmy_donaldson_320',
	'druuzil/jordan_peterson_384',
	'druuzil/karl_urban_224',
	'druuzil/kate_beckinsale_384',
	'druuzil/laurence_fishburne_384',
	'druuzil/lili_reinhart_320',
	'druuzil/mads_mikkelsen_384',
	'druuzil/mary_winstead_320',
	'druuzil/melina_juergens_320',
	'druuzil/michael_fassbender_320',
	'druuzil/michael_fox_320',
	'druuzil/millie_bobby_brown_320',
	'druuzil/morgan_freeman_320',
	'druuzil/patrick_stewart_320',
	'druuzil/rebecca_ferguson_320',
	'druuzil/scarlett_johansson_320',
	'druuzil/seth_macfarlane_384',
	'druuzil/thomas_cruise_320',
	'druuzil/thomas_hanks_384',
	'edel/emma_roberts_224',
	'edel/ivanka_trump_224',
	'edel/lize_dzjabrailova_224',
	'edel/sidney_sweeney_224',
	'edel/winona_ryder_224',
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
	'iperov/keanu_reeves_320',
	'iperov/margot_robbie_224',
	'iperov/natalie_dormer_224',
	'iperov/nicolas_coppola_224',
	'iperov/robert_downey_224',
	'iperov/rowan_atkinson_224',
	'iperov/ryan_reynolds_224',
	'iperov/scarlett_johansson_224',
	'iperov/sylvester_stallone_224',
	'iperov/thomas_cruise_224',
	'iperov/thomas_holland_224',
	'iperov/vin_diesel_224',
	'iperov/vladimir_putin_224',
	'jen/angelica_trae_288',
	'jen/ella_freya_224',
	'jen/emma_myers_320',
	'jen/evie_pickerill_224',
	'jen/kang_hyewon_320',
	'jen/maddie_mead_224',
	'jen/nicole_turnbull_288',
	'mats/alica_schmidt_320',
	'mats/ashley_alexiss_224',
	'mats/billie_eilish_224',
	'mats/brie_larson_224',
	'mats/cara_delevingne_224',
	'mats/carolin_kebekus_224',
	'mats/chelsea_clinton_224',
	'mats/claire_boucher_224',
	'mats/corinna_kopf_224',
	'mats/florence_pugh_224',
	'mats/hillary_clinton_224',
	'mats/jenna_fischer_224',
	'mats/kim_jisoo_320',
	'mats/mica_suarez_320',
	'mats/shailene_woodley_224',
	'mats/shraddha_kapoor_320',
	'mats/yu_jimin_352',
	'rumateus/alison_brie_224',
	'rumateus/amber_heard_224',
	'rumateus/angelina_jolie_224',
	'rumateus/aubrey_plaza_224',
	'rumateus/bridget_regan_224',
	'rumateus/cobie_smulders_224',
	'rumateus/deborah_woll_224',
	'rumateus/dua_lipa_224',
	'rumateus/emma_stone_224',
	'rumateus/hailee_steinfeld_224',
	'rumateus/hilary_duff_224',
	'rumateus/jessica_alba_224',
	'rumateus/jessica_biel_224',
	'rumateus/john_cena_224',
	'rumateus/kim_kardashian_224',
	'rumateus/kristen_bell_224',
	'rumateus/lucy_liu_224',
	'rumateus/margot_robbie_224',
	'rumateus/megan_fox_224',
	'rumateus/meghan_markle_224',
	'rumateus/millie_bobby_brown_224',
	'rumateus/natalie_portman_224',
	'rumateus/nicki_minaj_224',
	'rumateus/olivia_wilde_224',
	'rumateus/shay_mitchell_224',
	'rumateus/sophie_turner_224',
	'rumateus/taylor_swift_224'
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
	'deep_swapper_morph',
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
	'face_enhancer_weight',
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
	'deep_swapper_morph' : int,
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
	'face_enhancer_weight' : float,
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

AgeModifierDirection = NDArray[Any]
DeepSwapperMorph = NDArray[Any]
FaceEnhancerWeight = NDArray[Any]
LivePortraitPitch = float
LivePortraitYaw = float
LivePortraitRoll = float
LivePortraitExpression = NDArray[Any]
LivePortraitFeatureVolume = NDArray[Any]
LivePortraitMotionPoints = NDArray[Any]
LivePortraitRotation = NDArray[Any]
LivePortraitScale = NDArray[Any]
LivePortraitTranslation = NDArray[Any]
