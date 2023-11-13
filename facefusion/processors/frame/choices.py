from typing import List

import numpy

face_swapper_models : List[str] = [ 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial' ]
face_enhancer_models : List[str] = [ 'codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_512', 'restoreformer' ]
frame_enhancer_models : List[str] = [ 'real_esrgan_x2plus', 'real_esrgan_x4plus', 'real_esrnet_x4plus' ]

face_enhancer_blend_range : List[int] = numpy.arange(0, 101, 1).tolist()
frame_enhancer_blend_range : List[int] = numpy.arange(0, 101, 1).tolist()
