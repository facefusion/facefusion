from typing import List

from facefusion.common_helper import create_int_range
from facefusion.processors.frame.typings import FaceDebuggerItem, FaceEnhancerModel, FaceSwapperModel, FrameEnhancerModel, LipSyncerModel

face_debugger_items : List[FaceDebuggerItem] = [ 'bounding-box', 'face-landmark-5', 'face-landmark-5/68', 'face-landmark-68', 'face-mask', 'score', 'age', 'gender' ]
face_enhancer_models : List[FaceEnhancerModel] = [ 'codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'restoreformer_plus_plus' ]
face_swapper_models : List[FaceSwapperModel] = [ 'blendswap_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial', 'uniface_256' ]
frame_enhancer_models : List[FrameEnhancerModel] = [ 'lsdir_x4', 'lsdir_compact_2_x4', 'lsdir_compact_3_x4', 'lsdir_plus_c_x4', 'lsdir_plus_n_x4', 'lsdir_plus_r_x4', 'nomos8k_sc_4x', 'parimg_compact_x2', 'real_esrgan_128', 'real_esrgan_256', 'span_kendata_4x' ]
lip_syncer_models : List[LipSyncerModel] = [ 'wav2lip_gan' ]

face_enhancer_blend_range : List[int] = create_int_range(0, 100, 1)
frame_enhancer_blend_range : List[int] = create_int_range(0, 100, 1)
