from typing import Dict, List
from facefusion.common_helper import create_int_range
from facefusion.processors.frame.typing import FaceDebuggerItem, FaceEnhancerModel, FaceSwapperModel, FrameColorizerModel, FrameEnhancerModel, LipSyncerModel

face_debugger_items : List[FaceDebuggerItem] = [ 'bounding-box', 'face-landmark-5', 'face-landmark-5/68', 'face-landmark-68', 'face-landmark-68/5', 'face-mask', 'face-detector-score', 'face-landmarker-score', 'age', 'gender' ]
face_enhancer_models : List[FaceEnhancerModel] = [ 'codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'gpen_bfr_1024', 'gpen_bfr_2048', 'restoreformer_plus_plus' ]
face_swapper_set : Dict[FaceSwapperModel, List[str]] =\
{
	'blendswap_256': [ '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'inswapper_128': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'inswapper_128_fp16': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'simswap_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'simswap_512_unofficial': [ '512x512', '768x768', '1024x1024' ],
	'uniface_256': [ '256x256', '512x512', '768x768', '1024x1024' ]
}
frame_colorizer_models : List[FrameColorizerModel] = [ 'ddcolor', 'ddcolor_artistic', 'deoldify', 'deoldify_artistic', 'deoldify_stable' ]
frame_colorizer_sizes : List[str] = [ '192x192', '256x256', '384x384', '512x512' ]
frame_enhancer_models : List[FrameEnhancerModel] = [ 'clear_reality_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_hatgan_x4', 'span_kendata_x4', 'ultra_sharp_x4' ]
lip_syncer_models : List[LipSyncerModel] = [ 'wav2lip_gan' ]

face_enhancer_blend_range : List[int] = create_int_range(0, 100, 1)
frame_colorizer_blend_range : List[int] = create_int_range(0, 100, 1)
frame_enhancer_blend_range : List[int] = create_int_range(0, 100, 1)
