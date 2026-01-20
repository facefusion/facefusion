from facefusion.types import Locales

LOCALES : Locales =\
{
	'en':
	{
		'help':
		{
			'model': 'choose the model responsible for restoring the expression',
			'factor': 'restore factor of expression from the target face',
			'areas': 'choose the items used for the expression areas (choices: {choices})'
		},
		'uis':
		{
			'model_dropdown': 'EXPRESSION RESTORER MODEL',
			'factor_slider': 'EXPRESSION RESTORER FACTOR',
			'areas_checkbox_group': 'EXPRESSION RESTORER AREAS'
		}
	},
	'tr':
	{
		'help':
		{
			'model': 'ıfade geri yükleme için sorumlu modeli seçin',
			'factor': 'hedef yüzden ıfade geri yükleme faktörü',
			'areas': 'ıfade alanları için kullanılan öğeleri seçin (seçenekler: {choices})'
		},
		'uis':
		{
			'model_dropdown': 'İFADE GERİ YÜKLEYİCİ MODELİ',
			'factor_slider': 'İFADE GERİ YÜKLEYİCİ FAKTÖRÜ',
			'areas_checkbox_group': 'İFADE GERİ YÜKLEYİCİ ALANLARI'
		}
	}
}
