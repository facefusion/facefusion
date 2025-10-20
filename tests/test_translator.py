from facefusion import translator
from facefusion.locals import LOCALS


def test_load() -> None:
	translator.load(LOCALS, __name__)

	assert __name__ in translator.LOCAL_POOL_SET


def test_get() -> None:
	assert translator.get('conda_not_activated', 'facefusion') == 'conda is not activated'
	assert translator.get('help.skip_conda', 'facefusion') == 'skip the conda environment check'
	assert translator.get('invalid', 'facefusion') is None
