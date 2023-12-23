from typing import List

from facefusion.typing import FaceSelectorMode, FaceAnalyserOrder, FaceAnalyserAge, FaceAnalyserGender, FaceMaskType, FaceMaskRegion, TempFrameFormat, OutputVideoEncoder
from facefusion.common_helper import create_range

face_analyser_orders : List[FaceAnalyserOrder] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best' ]
face_analyser_ages : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_genders : List[FaceAnalyserGender] = [ 'male', 'female' ]
face_detector_models : List[str] = [ 'retinaface', 'yunet' ]
face_detector_sizes : List[str] = [ '160x160', '320x320', '480x480', '512x512', '640x640', '768x768', '960x960', '1024x1024' ]
face_selector_modes : List[FaceSelectorMode] = [ 'reference', 'one', 'many' ]
face_mask_types : List[FaceMaskType] = [ 'box', 'occlusion', 'region' ]
face_mask_regions : List[FaceMaskRegion] = [ 'skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'eye-glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip' ]
temp_frame_formats : List[TempFrameFormat] = [ 'jpg', 'png' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]

execution_thread_count_range : List[float] = create_range(1, 128, 1)
execution_queue_count_range : List[float] = create_range(1, 32, 1)
max_memory_range : List[float] = create_range(0, 128, 1)
face_detector_score_range : List[float] = create_range(0.0, 1.0, 0.05)
face_mask_blur_range : List[float] = create_range(0.0, 1.0, 0.05)
face_mask_padding_range : List[float] = create_range(0, 100, 1)
reference_face_distance_range : List[float] = create_range(0.0, 1.5, 0.05)
temp_frame_quality_range : List[float] = create_range(0, 100, 1)
output_image_quality_range : List[float] = create_range(0, 100, 1)
output_video_quality_range : List[float] = create_range(0, 100, 1)
