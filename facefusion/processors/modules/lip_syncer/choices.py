from typing import List, Sequence

from facefusion.common_helper import create_float_range
from facefusion.processors.modules.lip_syncer.types import LipSyncerModel

lip_syncer_models : List[LipSyncerModel] = [ 'edtalk_256', 'wav2lip_96', 'wav2lip_gan_96' ]

lip_syncer_weight_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
