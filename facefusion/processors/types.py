from typing import Any, Dict, Tuple, TypeAlias

from numpy.typing import NDArray

from facefusion.types import AppContext, Mask, VisionFrame

LivePortraitPitch : TypeAlias = float
LivePortraitYaw : TypeAlias = float
LivePortraitRoll : TypeAlias = float
LivePortraitExpression : TypeAlias = NDArray[Any]
LivePortraitFeatureVolume : TypeAlias = NDArray[Any]
LivePortraitMotionPoints : TypeAlias = NDArray[Any]
LivePortraitRotation : TypeAlias = NDArray[Any]
LivePortraitScale : TypeAlias = NDArray[Any]
LivePortraitTranslation : TypeAlias = NDArray[Any]

ProcessorStateKey = str
ProcessorState : TypeAlias = Dict[ProcessorStateKey, Any]
ProcessorStateSet : TypeAlias = Dict[AppContext, ProcessorState]
ProcessorOutputs : TypeAlias = Tuple[VisionFrame, Mask]
