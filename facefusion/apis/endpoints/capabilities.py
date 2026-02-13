from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

import facefusion.choices


async def get_capabilities(request : Request) -> JSONResponse:
	capabilities =\
	{
		'formats':
		{
			'audio': facefusion.choices.audio_formats,
			'image': facefusion.choices.image_formats,
			'video': facefusion.choices.video_formats
		}
	}
	return JSONResponse(capabilities, status_code = HTTP_200_OK)
