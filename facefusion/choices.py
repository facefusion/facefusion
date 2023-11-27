from typing import List

import numpy

from facefusion.typing import FaceSelectorMode, FaceAnalyserOrder, FaceAnalyserAge, FaceAnalyserGender, TempFrameFormat, OutputVideoEncoder


face_analyser_orders : List[FaceAnalyserOrder] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best' ]
face_analyser_ages : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_genders : List[FaceAnalyserGender] = [ 'male', 'female' ]
face_detector_models : List[str] = [ 'retinaface', 'yunet' ]
face_detector_sizes : List[str] = [ '160x160', '320x320', '480x480', '512x512', '640x640', '768x768', '960x960', '1024x1024' ]
face_selector_modes : List[FaceSelectorMode] = [ 'reference', 'one', 'many' ]
temp_frame_formats : List[TempFrameFormat] = [ 'jpg', 'png' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]

execution_thread_count_range : List[int] = numpy.arange(1, 129, 1).tolist()
execution_queue_count_range : List[int] = numpy.arange(1, 33, 1).tolist()
max_memory_range : List[int] = numpy.arange(0, 129, 1).tolist()
face_detector_score_range : List[float] = numpy.arange(0.0, 1.05, 0.05).tolist()
face_mask_blur_range : List[float] = numpy.arange(0.0, 1.05, 0.05).tolist()
face_mask_padding_range : List[float] = numpy.arange(0, 101, 1).tolist()
reference_face_distance_range : List[float] = numpy.arange(0.0, 1.55, 0.05).tolist()
temp_frame_quality_range : List[int] = numpy.arange(0, 101, 1).tolist()
output_image_quality_range : List[int] = numpy.arange(0, 101, 1).tolist()
output_video_quality_range : List[int] = numpy.arange(0, 101, 1).tolist()
