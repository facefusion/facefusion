from facefusion import wording


def test_get() -> None:
	assert wording.get('python_not_supported')
<<<<<<< HEAD
	assert wording.get('help.source')
=======
	assert wording.get('help.source_paths')
>>>>>>> origin/master
	assert wording.get('invalid') is None
