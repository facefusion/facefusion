from typing import List, Sequence

from facefusion.common_helper import create_int_range
from facefusion.processors.modules.frame_enhancer.types import FrameEnhancerModel

frame_enhancer_models : List[FrameEnhancerModel] = [ 'clear_reality_x4', 'face_dat_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_esrgan_x8', 'real_esrgan_x8_fp16', 'real_hatgan_x4', 'real_web_photo_x4', 'realistic_rescaler_x4', 'remacri_x4', 'siax_x4', 'span_kendata_x4', 'swin2_sr_x4', 'tghq_face_x8', 'ultra_sharp_x4', 'ultra_sharp_2_x4' ]

frame_enhancer_blend_range : Sequence[int] = create_int_range(0, 100, 1)
