from facefusion import translator
from facefusion.locales import LOCALES


def test_autoload() -> None:
	translator.__autoload__('facefusion.processors.modules.face_debugger')
	translator.__autoload__('invalid')

	assert translator.LOCALE_POOL_SET.get('facefusion.processors.modules.face_debugger').get('en').get('help').get('items') == 'load a single or multiple processors (choices: {choices})'
	assert translator.LOCALE_POOL_SET.get('invalid') is None


def test_load() -> None:
	translator.load(LOCALES, __name__)

	assert translator.LOCALE_POOL_SET.get(__name__) == LOCALES


def test_get() -> None:
	assert translator.get('processing_stopped') == 'processing stopped'
	assert translator.get('help.run') == 'run the program'
	assert translator.get('help.model', 'facefusion.processors.modules.face_swapper') == 'choose the model responsible for swapping the face'
	assert translator.get('help.invalid') is None
	assert translator.get('invalid') is None
