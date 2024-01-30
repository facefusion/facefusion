from typing import Literal

FaceDebuggerItem = Literal['bbox', 'kps', 'face-mask', 'score']
FaceEnhancerModel = Literal['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'restoreformer_plus_plus']
FaceSwapperModel = Literal['blendswap_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial']
FrameEnhancerModel = Literal['real_esrgan_x2plus', 'real_esrgan_x4plus', 'real_esrnet_x4plus']
