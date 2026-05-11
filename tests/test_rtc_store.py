import pytest

from facefusion import environment, state_manager
from facefusion.libraries import datachannel as datachannel_module, opus as opus_module, vpx as vpx_module


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])

	environment.setup_platform()

	datachannel_module.pre_check()
	opus_module.pre_check()
	vpx_module.pre_check()


# TODO: test create_rtc_stream, get_rtc_stream, destroy_rtc_stream lifecycle
def test_rtc_stream_lifecycle() -> None:
	pass


# TODO: test add_rtc_viewer with valid session and sdp offer
def test_add_rtc_viewer() -> None:
	pass
