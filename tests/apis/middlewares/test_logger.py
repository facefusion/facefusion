from unittest.mock import AsyncMock, patch

import pytest
from starlette.types import Scope

from facefusion.apis.middlewares.logger import send_with_log


@pytest.mark.asyncio
async def test_send_with_log() -> None:
	scope : Scope =\
	{
		'method': 'POST',
		'path': '/assets'
	}
	send_mock = AsyncMock()

	with patch('facefusion.logger.info') as info_mock:
		await send_with_log(scope, send_mock,
		{
			'type': 'http.response.start',
			'status': 201
		})

		assert info_mock.call_args.args == ('POST /assets 201', 'facefusion.apis.request')

		await send_with_log(scope, send_mock,
		{
			'type': 'http.response.body'
		})

		assert info_mock.call_count == 1

	assert send_mock.await_count == 2
