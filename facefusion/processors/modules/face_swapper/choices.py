from typing import List, Sequence

from facefusion.common_helper import create_float_range
from facefusion.processors.modules.face_swapper.types import FaceSwapperModel, FaceSwapperSet, FaceSwapperWeight

face_swapper_set : FaceSwapperSet =\
{
	'blendswap_256': [ '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'ghost_1_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'ghost_2_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'ghost_3_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hififace_unofficial_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1a_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1b_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'hyperswap_1c_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'inswapper_128': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'inswapper_128_fp16': [ '128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024' ],
	'simswap_256': [ '256x256', '512x512', '768x768', '1024x1024' ],
	'simswap_unofficial_512': [ '512x512', '768x768', '1024x1024' ],
	'uniface_256': [ '256x256', '512x512', '768x768', '1024x1024' ]
}

face_swapper_models : List[FaceSwapperModel] = list(face_swapper_set.keys())

face_swapper_weight_range : Sequence[FaceSwapperWeight] = create_float_range(0.0, 1.0, 0.05)
