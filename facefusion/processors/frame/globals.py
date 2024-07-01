from typing import Optional

from facefusion.processors.frame.typing import FrameColorizerModel, FrameEnhancerModel, LipSyncerModel

frame_colorizer_model : Optional[FrameColorizerModel] = None
frame_colorizer_blend : Optional[int] = None
frame_colorizer_size : Optional[str] = None
frame_enhancer_model : Optional[FrameEnhancerModel] = None
frame_enhancer_blend : Optional[int] = None
lip_syncer_model : Optional[LipSyncerModel] = None
