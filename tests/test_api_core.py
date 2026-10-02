from unittest.mock import patch

import pytest

from facefusion import content_analyser, state_manager
from facefusion.apis.core import get_common_modules, pre_check
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, opus as opus_module, vpx as vpx_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('execution_device_ids', [ 0 ])
	state_manager.init_item('execution_providers', [ 'cpu' ])
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])


def test_get_common_modules() -> None:
	assert get_common_modules() == [ aom_module, content_analyser, datachannel_module, opus_module, vpx_module ]


def test_pre_check() -> None:
	assert pre_check() is True

	with patch('facefusion.content_analyser.pre_check', return_value = False):
		assert pre_check() is False
