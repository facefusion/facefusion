from facefusion import translator
from facefusion.locales import LOCALES


def test_load() -> None:
	translator.load(LOCALES, __name__)

	assert __name__ in translator.LOCALE_POOL_SET


def test_get() -> None:
	assert translator.get('processing_stopped') == 'processing stopped'
	assert translator.get('help.run') == 'run the program'
	assert translator.get('invalid') is None
