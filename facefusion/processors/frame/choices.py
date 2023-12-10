from typing import List
import numpy

from facefusion.processors.frame.typings import FaceSwapperModel, FaceEnhancerModel, FrameEnhancerModel, FaceDebuggerItem

face_swapper_models : List[FaceSwapperModel] = [ 'blendswap_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial' ]
face_enhancer_models : List[FaceEnhancerModel] = [ 'codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'restoreformer' ]
frame_enhancer_models : List[FrameEnhancerModel] = [ 'real_esrgan_x2plus', 'real_esrgan_x4plus', 'real_esrnet_x4plus' ]

face_enhancer_blend_range : List[int] = numpy.arange(0, 101, 1).tolist()
frame_enhancer_blend_range : List[int] = numpy.arange(0, 101, 1).tolist()

face_debugger_items : List[FaceDebuggerItem] = [ 'bbox', 'kps', 'face-mask', 'score' ]
