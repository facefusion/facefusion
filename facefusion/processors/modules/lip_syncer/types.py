from typing import Any, Literal, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.types import AudioFrame, Mask, VisionFrame

LipSyncerInputs = TypedDict('LipSyncerInputs',
{
	'reference_vision_frame' : VisionFrame,
	'source_voice_frame' : AudioFrame,
	'target_vision_frame' : VisionFrame,
	'temp_vision_frame' : VisionFrame,
	'temp_vision_mask' : Mask
})

LipSyncerModel = Literal['edtalk_256', 'wav2lip_96', 'wav2lip_gan_96']

LipSyncerWeight : TypeAlias = NDArray[Any]
