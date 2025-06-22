from typing import List, Sequence

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.filesystem import get_file_name, resolve_file_paths, resolve_relative_path
from facefusion.processors.types import AgeModifierModel, DeepSwapperModel, ExpressionRestorerModel, FaceDebuggerItem, FaceEditorModel, FaceEnhancerModel, FaceSwapperModel, FaceSwapperSet, FrameColorizerModel, FrameEnhancerModel, LipSyncerModel

age_modifier_models : List[AgeModifierModel] = [ 'styleganex_age' ]
deep_swapper_models : List[DeepSwapperModel] =\
[
	'druuzil/adam_levine_320',
	'druuzil/adrianne_palicki_384',
	'druuzil/agnetha_falskog_224',
	'druuzil/alan_ritchson_320',
	'druuzil/alicia_vikander_320',
	'druuzil/amber_midthunder_320',
	'druuzil/andras_arato_384',
	'druuzil/andrew_tate_320',
	'druuzil/angelina_jolie_384',
	'druuzil/anne_hathaway_320',
	'druuzil/anya_chalotra_320',
	'druuzil/arnold_schwarzenegger_320',
	'druuzil/benjamin_affleck_320',
	'druuzil/benjamin_stiller_384',
	'druuzil/bradley_pitt_224',
	'druuzil/brie_larson_384',
	'druuzil/bruce_campbell_384',
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
	'druuzil/james_carrey_384',
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
	'druuzil/luke_evans_384',
	'druuzil/mads_mikkelsen_384',
	'druuzil/mary_winstead_320',
	'druuzil/margaret_qualley_384',
	'druuzil/melina_juergens_320',
	'druuzil/michael_fassbender_320',
	'druuzil/michael_fox_320',
	'druuzil/millie_bobby_brown_320',
	'druuzil/morgan_freeman_320',
	'druuzil/patrick_stewart_224',
	'druuzil/rachel_weisz_384',
	'druuzil/rebecca_ferguson_320',
	'druuzil/scarlett_johansson_320',
	'druuzil/shannen_doherty_384',
	'druuzil/seth_macfarlane_384',
	'druuzil/thomas_cruise_320',
	'druuzil/thomas_hanks_384',
	'druuzil/william_murray_384',
	'druuzil/zoe_saldana_384',
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

custom_model_file_paths = resolve_file_paths(resolve_relative_path('../.assets/models/custom'))

if custom_model_file_paths:

	for model_file_path in custom_model_file_paths:
		model_id = '/'.join([ 'custom', get_file_name(model_file_path) ])
		deep_swapper_models.append(model_id)

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
	'hififace_unofficial_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1a_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1b_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1c_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'inswapper_128': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'inswapper_128_fp16': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'simswap_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'simswap_unofficial_512': [ '512x512', '768x768', '1024x1024' ],
	'uniface_256': [ '256x256', '512x512', '768x768', '1024x1024' ]
}
face_swapper_models : List[FaceSwapperModel] = list(face_swapper_set.keys())
frame_colorizer_models : List[FrameColorizerModel] = [ 'ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable' ]
frame_colorizer_sizes : List[str] = [ '192x192', '256x256', '384x384', '512x512' ]
frame_enhancer_models : List[FrameEnhancerModel] = [ 'clear_reality_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_esrgan_x8', 'real_esrgan_x8_fp16', 'real_hatgan_x4', 'real_web_photo_x4', 'realistic_rescaler_x4', 'remacri_x4', 'siax_x4', 'span_kendata_x4', 'swin2_sr_x4', 'ultra_sharp_x4', 'ultra_sharp_2_x4' ]
lip_syncer_models : List[LipSyncerModel] = [ 'edtalk_256', 'wav2lip_96', 'wav2lip_gan_96' ]

age_modifier_direction_range : Sequence[int] = create_int_range(-100, 100, 1)
deep_swapper_morph_range : Sequence[int] = create_int_range(0, 100, 1)
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
face_enhancer_weight_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
frame_colorizer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
frame_enhancer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
lip_syncer_weight_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
