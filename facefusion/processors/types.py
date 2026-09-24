import importlib
from typing import Any, Callable, Tuple, TypeAlias, TypedDict

from numpy.typing import NDArray

from facefusion.filesystem import get_file_name, resolve_file_paths
from facefusion.types import Mask, VisionFrame

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
ProcessorStateKey : TypeAlias = Any

ProcessorState = TypedDict('ProcessorState', {})

for file_path in resolve_file_paths('facefusion/processors/modules'):
	ProcessorState.__annotations__.update(importlib.import_module('facefusion.processors.modules.' + get_file_name(file_path) + '.types').State.__annotations__)

ApplyStateItem : TypeAlias = Callable[[ProcessorStateKey, ProcessorStateValue], None]

ProcessorOutputs : TypeAlias = Tuple[VisionFrame, Mask]
