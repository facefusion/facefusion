from typing import List, Optional

from facefusion.typing import OutputAudioEncoder, OutputVideoEncoder, OutputVideoPreset

# output creation
output_image_quality : Optional[int] = None
output_image_resolution : Optional[str] = None
output_audio_encoder : Optional[OutputAudioEncoder] = None
output_video_encoder : Optional[OutputVideoEncoder] = None
output_video_preset : Optional[OutputVideoPreset] = None
output_video_quality : Optional[int] = None
output_video_resolution : Optional[str] = None
output_video_fps : Optional[float] = None
skip_audio : Optional[bool] = None
# frame processors
frame_processors : List[str] = []
