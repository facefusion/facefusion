<<<<<<< HEAD
METADATA =\
{
	'name': 'FaceFusion',
	'description': 'Next generation face swapper and enhancer',
	'version': '2.6.0',
=======
from typing import Optional

METADATA =\
{
	'name': 'FaceFusion',
	'description': 'Industry leading face manipulation platform',
	'version': '3.1.1',
>>>>>>> origin/master
	'license': 'MIT',
	'author': 'Henry Ruhs',
	'url': 'https://facefusion.io'
}


<<<<<<< HEAD
def get(key : str) -> str:
	return METADATA[key]
=======
def get(key : str) -> Optional[str]:
	if key in METADATA:
		return METADATA.get(key)
	return None
>>>>>>> origin/master
