from typing import Any, Callable, Dict, Tuple, TypeAlias

from numpy.typing import NDArray

from facefusion.types import AppContext, Mask, SessionId, VisionFrame

LivePortraitPitch : TypeAlias = float
LivePortraitYaw : TypeAlias = float
LivePortraitRoll : TypeAlias = float
LivePortraitExpression : TypeAlias = NDArray[Any]
LivePortraitFeatureVolume : TypeAlias = NDArray[Any]
LivePortraitMotionPoints : TypeAlias = NDArray[Any]
LivePortraitRotation : TypeAlias = NDArray[Any]
LivePortraitScale : TypeAlias = NDArray[Any]
LivePortraitTranslation : TypeAlias = NDArray[Any]

ProcessorStateValue : TypeAlias = Any
ProcessorStateKey : TypeAlias = str
ProcessorState : TypeAlias = Dict[ProcessorStateKey, ProcessorStateValue]
ProcessorSessionStateSet : TypeAlias = Dict[SessionId, ProcessorState]
ProcessorStateSet : TypeAlias = Dict[AppContext, ProcessorSessionStateSet]

ApplyStateItem : TypeAlias = Callable[[ProcessorStateKey, ProcessorStateValue], None]

ProcessorOutputs : TypeAlias = Tuple[VisionFrame, Mask]
