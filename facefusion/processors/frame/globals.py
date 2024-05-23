from typing import List, Optional

from facefusion.processors.frame.typings import FaceDebuggerItem, FaceEnhancerModel, FaceSwapperModel, FrameColorizerModel, FrameEnhancerModel, LipSyncerModel

face_debugger_items : Optional[List[FaceDebuggerItem]] = None
face_enhancer_model : Optional[FaceEnhancerModel] = None
face_enhancer_blend : Optional[int] = None
face_swapper_model : Optional[FaceSwapperModel] = None
frame_colorizer_model : Optional[FrameColorizerModel] = None
frame_colorizer_blend : Optional[int] = None
frame_colorizer_size : Optional[str] = None
frame_enhancer_model : Optional[FrameEnhancerModel] = None
frame_enhancer_blend : Optional[int] = None
lip_syncer_model : Optional[LipSyncerModel] = None
