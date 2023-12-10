from typing import Literal

FaceSwapperModel = Literal['blendswap_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial']
FaceEnhancerModel = Literal['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'restoreformer']
FrameEnhancerModel = Literal['real_esrgan_x2plus', 'real_esrgan_x4plus', 'real_esrnet_x4plus']

FaceDebuggerItem = Literal['bbox', 'kps', 'face-mask', 'score']
