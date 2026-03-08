from typing import List, get_args

from facefusion.processors.modules.face_debugger.types import FaceDebuggerItem

face_debugger_items : List[FaceDebuggerItem] = list(get_args(FaceDebuggerItem))
