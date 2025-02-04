from typing import List, Dict

from facefusion.typing import VideoMemoryStrategy, FaceSelectorMode, FaceAnalyserOrder, FaceAnalyserAge, FaceAnalyserGender, FaceDetectorModel, FaceMaskType, FaceMaskRegion, TempFrameFormat, OutputVideoEncoder, OutputVideoPreset
from facefusion.common_helper import create_int_range, create_float_range

video_memory_strategies : List[VideoMemoryStrategy] = [ 'strict', 'moderate', 'tolerant' ]
face_analyser_orders : List[FaceAnalyserOrder] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best' ]
face_analyser_ages : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_genders : List[FaceAnalyserGender] = [ 'female', 'male' ]
face_detector_set : Dict[FaceDetectorModel, List[str]] =\
{
	'many': [ '640x640' ],
	'retinaface': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'scrfd': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'yoloface': [ '640x640' ],
	'yunet': [ '160x160', '320x320', '480x480', '512x512', '640x640', '768x768', '960x960', '1024x1024' ]
}
face_selector_modes : List[FaceSelectorMode] = [ 'many', 'one', 'reference' ]
face_mask_types : List[FaceMaskType] = [ 'box', 'occlusion', 'region' ]
face_mask_regions : List[FaceMaskRegion] = [ 'skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip' ]
temp_frame_formats : List[TempFrameFormat] = [ 'bmp', 'jpg', 'png' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf' ]
output_video_presets : List[OutputVideoPreset] = [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow' ]

image_template_sizes : List[float] = [ 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4 ]
video_template_sizes : List[int] = [ 240, 360, 480, 540, 720, 1080, 1440, 2160, 4320 ]

execution_thread_count_range : List[int] = create_int_range(1, 128, 1)
execution_queue_count_range : List[int] = create_int_range(1, 32, 1)
system_memory_limit_range : List[int] = create_int_range(0, 128, 1)
face_detector_score_range : List[float] = create_float_range(0.0, 1.0, 0.05)
face_landmarker_score_range : List[float] = create_float_range(0.0, 1.0, 0.05)
face_mask_blur_range : List[float] = create_float_range(0.0, 1.0, 0.05)
face_mask_padding_range : List[int] = create_int_range(0, 100, 1)
reference_face_distance_range : List[float] = create_float_range(0.0, 1.5, 0.05)
output_image_quality_range : List[int] = create_int_range(0, 100, 1)
output_video_quality_range : List[int] = create_int_range(0, 100, 1)
