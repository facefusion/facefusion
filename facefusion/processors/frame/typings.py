from typing import Literal, TypedDict

from facefusion.typing import Face, FaceSet, AudioFrame, VisionFrame

FaceDebuggerItem = Literal['bbox', 'kps', 'face-mask', 'score', 'age', 'gender']
FaceEnhancerModel = Literal['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'restoreformer_plus_plus']
FaceSwapperModel = Literal['blendswap_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_512_unofficial']
FrameEnhancerModel = Literal['real_esrgan_x2plus', 'real_esrgan_x4plus', 'real_esrnet_x4plus']
LipSyncerModel = Literal['wav2lip']

FaceDebuggerInputs = TypedDict('FaceDebuggerInputs',
{
	'target_vision_frame' : VisionFrame,
	'reference_faces' : FaceSet
})
FaceEnhancerInputs = TypedDict('FaceEnhancerInputs',
{
	'target_vision_frame' : VisionFrame,
	'reference_faces' : FaceSet,
})
FaceSwapperInputs = TypedDict('FaceSwapperInputs',
{
	'source_face' : Face,
	'target_vision_frame' : VisionFrame,
	'reference_faces' : FaceSet,
})
FrameEnhancerInputs = TypedDict('FrameEnhancerInputs',
{
	'target_vision_frame' : VisionFrame
})
LipSyncerInputs = TypedDict('LipSyncerInputs',
{
	'source_audio_frame' : AudioFrame,
	'target_vision_frame' : VisionFrame,
	'reference_faces': FaceSet,
})
