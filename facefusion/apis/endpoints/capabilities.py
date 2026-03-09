from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

import facefusion.choices
from facefusion import capability_store
from facefusion.execution import get_available_execution_providers
from facefusion.processors.modules.face_swapper import choices as face_swapper_choices


async def get_capabilities(request : Request) -> JSONResponse:
	capabilities =\
	{
		'formats':
		{
			'audio': facefusion.choices.audio_formats,
			'image': facefusion.choices.image_formats,
			'video': facefusion.choices.video_formats
		},
		'arguments': capability_store.get_api_capability_set(),
		'choices':
		{
			'execution_providers': get_available_execution_providers(),
			'face_detector_models': facefusion.choices.face_detector_models,
			'face_selector_modes': facefusion.choices.face_selector_modes,
			'face_selector_orders': facefusion.choices.face_selector_orders,
			'face_selector_genders': facefusion.choices.face_selector_genders,
			'face_selector_races': facefusion.choices.face_selector_races,
			'face_mask_types': facefusion.choices.face_mask_types,
			'face_detector_angles': list(facefusion.choices.face_detector_angles),
			'face_swapper_models': face_swapper_choices.face_swapper_models
		}
	}
	return JSONResponse(capabilities, status_code = HTTP_200_OK)
