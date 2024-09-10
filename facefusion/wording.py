from typing import Any, Dict, Optional

WORDING : Dict[str, Any] =\
{
	'conda_not_activated': 'Conda не активирован',
	'python_not_supported': 'Версия Python не поддерживается, обновите до {version} или выше',
	'ffmpeg_not_installed': 'FFMpeg не установлен',
	'creating_temp': 'Создание временных ресурсов',
	'extracting_frames': 'Извлечение кадров с разрешением {resolution} и {fps} кадров в секунду',
	'extracting_frames_succeed': 'Извлечение кадров успешно завершено',
	'extracting_frames_failed': 'Извлечение кадров завершилось неудачей',
	'analysing': 'Анализ',
	'processing': 'Обработка',
	'downloading': 'Загрузка',
	'temp_frames_not_found': 'Временные кадры не найдены',
	'copying_image': 'Копирование изображения с разрешением {resolution}',
	'copying_image_succeed': 'Копирование изображения завершено успешно',
	'copying_image_failed': 'Копирование изображения завершилось неудачей',
	'finalizing_image': 'Окончательная обработка изображения с разрешением {resolution}',
	'finalizing_image_succeed': 'Окончательная обработка изображения завершена успешно',
	'finalizing_image_skipped': 'Окончательная обработка изображения пропущена',
	'merging_video': 'Слияние видео с разрешением {resolution} и {fps} кадров в секунду',
	'merging_video_succeed': 'Слияние видео завершено успешно',
	'merging_video_failed': 'Слияние видео завершилось неудачей',
	'skipping_audio': 'Пропуск звука',
	'restoring_audio_succeed': 'Восстановление звука завершено успешно',
	'restoring_audio_skipped': 'Восстановление звука пропущено',
	'clearing_temp': 'Очистка временных ресурсов',
	'processing_stopped': 'Обработка остановлена',
	'processing_image_succeed': 'Обработка изображения завершена успешно за {seconds} секунд',
	'processing_image_failed': 'Обработка изображения завершилась неудачей',
	'processing_video_succeed': 'Обработка видео завершена успешно за {seconds} секунд',
	'processing_video_failed': 'Обработка видео завершилась неудачей',
	'model_download_not_done': 'Загрузка модели не завершена',
	'model_file_not_present': 'Файл модели отсутствует',
	'select_image_source': 'Выберите изображение для исходного пути',
	'select_audio_source': 'Выберите аудио для исходного пути',
	'select_video_target': 'Выберите видео для целевого пути',
	'select_image_or_video_target': 'Выберите изображение или видео для целевого пути',
	'select_file_or_directory_output': 'Выберите файл или каталог для пути к выводу',
	'no_source_face_detected': 'Исходное лицо не обнаружено',
	'frame_processor_not_loaded': 'Процессор кадров {frame_processor} не удалось загрузить',
	'frame_processor_not_implemented': 'Процессор кадров {frame_processor} не реализован правильно',
	'ui_layout_not_loaded': 'Макет пользовательского интерфейса {ui_layout} не удалось загрузить',
	'ui_layout_not_implemented': 'Макет пользовательского интерфейса {ui_layout} не реализован правильно',
	'stream_not_loaded': 'Поток {stream_mode} не удалось загрузить',
	'point': '.',
	'comma': ',',
	'colon': ':',
	'question_mark': '?',
	'exclamation_mark': '!',
	'help':
	{
		# installer
		'install_dependency': 'выберите вариант {dependency} для установки',
		'skip_conda': 'пропустить проверку среды conda',
		# general
		'config': 'выберите файл конфигурации для переопределения значений по умолчанию',
		'source': 'выберите одно или несколько исходных изображений или аудио',
		'target': 'выберите одно целевое изображение или видео',
		'output': 'указание выходного файла или каталога',
		# misc
		'force_download': 'принудительно запустить автоматическую загрузку и выход',
		'skip_download': 'исключить автоматическую загрузку и удаленный поиск',
		'headless': 'запустить программу без графического интерфейса',
		'log_level': 'регулировка степени важности сообщений, отображаемых в терминале',
		# execution
		'execution_device_id': 'указание устройства, используемого для обработки',
		'execution_providers': 'ускорение вывода модели с использованием различных провайдеров (варианты: {choices}, ...)',
		'execution_thread_count': 'указание количества параллельных потоков во время обработки',
		'execution_queue_count': 'указание количества кадров, обрабатываемых каждым потоком',
		# memory
		'video_memory_strategy': 'балансировка быстрой обработки кадров и низкого использования видеопамяти',
		'system_memory_limit': 'ограничение доступной оперативной памяти, которая может использоваться во время обработки',
		# face analyser
		'face_analyser_order': 'указание порядка, в котором анализатор лица обнаруживает лица',
		'face_analyser_age': 'фильтрация обнаруженных лиц по их возрасту',
		'face_analyser_gender': 'фильтрация обнаруженных лиц по их полу',
		'face_detector_model': 'выберите модель, отвечающую за обнаружение лица',
		'face_detector_size': 'указание размера кадра, предоставляемого детектору лица',
		'face_detector_score': 'фильтрация обнаруженных лиц по уровню достоверности',
		'face_landmarker_score': 'фильтрация обнаруженных контрольных точек по уровню достоверности',
		# face selector
		'face_selector_mode': 'использование отслеживания на основе ссылки или простого сопоставления',
		'reference_face_position': 'указание позиции, используемой для создания эталонного лица',
		'reference_face_distance': 'указание желаемого сходства между эталонным лицом и целевым лицом',
		'reference_frame_number': 'указание кадра, используемого для создания эталонного лица',
		# face mask
		'face_mask_types': 'смешивание и сопоставление различных типов масок лица (варианты: {choices})',
		'face_mask_blur': 'указание степени размытия, применяемого к маске рамки',
		'face_mask_padding': 'применение верхнего, правого, нижнего и левого отступов к маске рамки',
		'face_mask_regions': 'выбор лицевых признаков, используемых для маски области (варианты: {choices})',
		# frame extraction
		'trim_frame_start': 'указание начального кадра целевого видео',
		'trim_frame_end': 'указание конечного кадра целевого видео',
		'temp_frame_format': 'указание формата временных ресурсов',
		'keep_temp': 'сохранение временных ресурсов после обработки',
		# output creation
		'output_image_quality': 'указание качества изображения, которое соответствует коэффициенту сжатия',
		'output_image_resolution': 'указание разрешения выходного изображения на основе целевого изображения',
		'output_video_encoder': 'указание кодировщика, используемого для сжатия видео',
		'output_video_preset': 'балансировка быстрой обработки видео и размера видеофайла',
		'output_video_quality': 'указание качества видео, которое соответствует коэффициенту сжатия',
		'output_video_resolution': 'указание разрешения выходного видео на основе целевого видео',
		'output_video_fps': 'указание частоты кадров выходного видео на основе целевого видео',
		'skip_audio': 'исключение звука из целевого видео',
		# frame processors
		'frame_processors': 'загрузка одного или нескольких процессоров кадров. (варианты: {choices}, ...)',
		'face_debugger_items': 'загрузка одного или нескольких процессоров кадров (варианты: {choices})',
		'face_enhancer_model': 'выберите модель, отвечающую за улучшение лица',
		'face_enhancer_blend': 'смешивание улучшенного лица с предыдущим',
		'face_swapper_model': 'выберите модель, отвечающую за замену лица',
		'frame_colorizer_model': 'выберите модель, отвечающую за раскрашивание кадра',
		'frame_colorizer_blend': 'смешивание раскрашенного кадра с предыдущим',
		'frame_colorizer_size': 'указание размера кадра, предоставляемого раскрашивателю кадров',
		'frame_enhancer_model': 'выберите модель, отвечающую за улучшение кадра',
		'frame_enhancer_blend': 'смешивание улучшенного кадра с предыдущим',
		'lip_syncer_model': 'выберите модель, отвечающую за синхронизацию губ',
		# uis
		'open_browser': 'открыть браузер после готовности программы',
		'ui_layouts': 'запуск одного или нескольких макетов пользовательского интерфейса (варианты: {choices}, ...)'
	},
	'uis':
	{
		# general
		'start_button': 'ПУСК',
		'stop_button': 'СТОП',
		'clear_button': 'ОЧИСТИТЬ',
		# about
		'donate_button': 'ПОЖЕРТВОВАТЬ',
		# benchmark
		'benchmark_results_dataframe': 'РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ',
		# benchmark options
		'benchmark_runs_checkbox_group': 'ЗАПУСКИ ТЕСТИРОВАНИЯ',
		'benchmark_cycles_slider': 'ЦИКЛЫ ТЕСТИРОВАНИЯ',
		# common options
		'common_options_checkbox_group': 'ВАРИАНТЫ',
		# execution
		'execution_providers_checkbox_group': 'ПОСТАВЩИКИ ВЫПОЛНЕНИЯ',
		# execution queue count
		'execution_queue_count_slider': 'КОЛИЧЕСТВО ОЧЕРЕДЕЙ ВЫПОЛНЕНИЯ',
		# execution thread count
		'execution_thread_count_slider': 'КОЛИЧЕСТВО ПОТОКОВ ВЫПОЛНЕНИЯ',
		# face analyser
		'face_analyser_order_dropdown': 'ПОРЯДОК АНАЛИЗАТОРА ЛИЦА',
		'face_analyser_age_dropdown': 'ВОЗРАСТ АНАЛИЗАТОРА ЛИЦА',
		'face_analyser_gender_dropdown': 'ПОЛ АНАЛИЗАТОРА ЛИЦА',
		'face_detector_model_dropdown': 'МОДЕЛЬ ДЕТЕКТОРА ЛИЦА',
		'face_detector_size_dropdown': 'РАЗМЕР ДЕТЕКТОРА ЛИЦА',
		'face_detector_score_slider': 'УРОВЕНЬ ДОСТОВЕРНОСТИ ДЕТЕКТОРА ЛИЦА',
		'face_landmarker_score_slider': 'УРОВЕНЬ ДОСТОВЕРНОСТИ ОПРЕДЕЛЕНИЯ КОНТРОЛЬНЫХ ТОЧЕК',
		# face masker
		'face_mask_types_checkbox_group': 'ТИПЫ МАСОК ЛИЦА',
		'face_mask_blur_slider': 'РАЗМЫТИЕ МАСКИ ЛИЦА',
		'face_mask_padding_top_slider': 'ВЕРХНИЙ ОТСТУП МАСКИ ЛИЦА',
		'face_mask_padding_right_slider': 'ПРАВЫЙ ОТСТУП МАСКИ ЛИЦА',
		'face_mask_padding_bottom_slider': 'НИЖНИЙ ОТСТУП МАСКИ ЛИЦА',
		'face_mask_padding_left_slider': 'ЛЕВЫЙ ОТСТУП МАСКИ ЛИЦА',
		'face_mask_region_checkbox_group': 'ОБЛАСТИ МАСКИ ЛИЦА',
		# face selector
		'face_selector_mode_dropdown': 'РЕЖИМ СЕЛЕКТОРА ЛИЦА',
		'reference_face_gallery': 'ЭТАЛОННОЕ ЛИЦО',
		'reference_face_distance_slider': 'РАССТОЯНИЕ ЭТАЛОННОГО ЛИЦА',
		# frame processors
		'frame_processors_checkbox_group': 'ПРОЦЕССОРЫ КАДРОВ',
		# frame processors options
		'face_debugger_items_checkbox_group': 'ЭЛЕМЕНТЫ ОТЛАДЧИКА ЛИЦА',
		'face_enhancer_model_dropdown': 'МОДЕЛЬ УЛУЧШЕНИЯ ЛИЦА',
		'face_enhancer_blend_slider': 'СМЕШИВАНИЕ УЛУЧШЕННОГО ЛИЦА',
		'face_swapper_model_dropdown': 'МОДЕЛЬ ЗАМЕНЫ ЛИЦА',
		'frame_colorizer_model_dropdown': 'МОДЕЛЬ РАСКРАШИВАНИЯ КАДРА',
		'frame_colorizer_blend_slider': 'СМЕШИВАНИЕ РАСКРАШЕННОГО КАДРА',
		'frame_colorizer_size_dropdown': 'РАЗМЕР РАСКРАШИВАТЕЛЯ КАДРА',
		'frame_enhancer_model_dropdown': 'МОДЕЛЬ УЛУЧШЕНИЯ КАДРА',
		'frame_enhancer_blend_slider': 'СМЕШИВАНИЕ УЛУЧШЕННОГО КАДРА',
		'lip_syncer_model_dropdown': 'МОДЕЛЬ СИНХРОНИЗАЦИИ ГУБ',
		# memory
		'video_memory_strategy_dropdown': 'СТРАТЕГИЯ ВИДЕОПАМЯТИ',
		'system_memory_limit_slider': 'ОГРАНИЧЕНИЕ СИСТЕМНОЙ ПАМЯТИ',
		# output
		'output_image_or_video': 'ВЫВОД',
		# output options
		'output_path_textbox': 'ПУТЬ К ВЫВОДУ',
		'output_image_quality_slider': 'КАЧЕСТВО ВЫХОДНОГО ИЗОБРАЖЕНИЯ',
		'output_image_resolution_dropdown': 'РАЗРЕШЕНИЕ ВЫХОДНОГО ИЗОБРАЖЕНИЯ',
		'output_video_encoder_dropdown': 'КОДИРОВЩИК ВЫХОДНОГО ВИДЕО',
		'output_video_preset_dropdown': 'ПРЕДУСТАНОВКА ВЫХОДНОГО ВИДЕО',
		'output_video_quality_slider': 'КАЧЕСТВО ВЫХОДНОГО ВИДЕО',
		'output_video_resolution_dropdown': 'РАЗРЕШЕНИЕ ВЫХОДНОГО ВИДЕО',
		'output_video_fps_slider': 'ЧАСТОТА КАДРОВ ВЫХОДНОГО ВИДЕО',
		# preview
		'preview_image': 'ПРЕДПРОСМОТР',
		'preview_frame_slider': 'КАДР ПРЕДПРОСМОТРА',
		# source
		'source_file': 'ИСТОЧНИК',
		# target
		'target_file': 'ЦЕЛЬ',
		# temp frame
		'temp_frame_format_dropdown': 'ФОРМАТ ВРЕМЕННОГО КАДРА',
		# trim frame
		'trim_frame_start_slider': 'НАЧАЛЬНЫЙ КАДР ОБРЕЗКИ',
		'trim_frame_end_slider': 'КОНЕЧНЫЙ КАДР ОБРЕЗКИ',
		# webcam
		'webcam_image': 'ВЕБ-КАМЕРА',
		# webcam options
		'webcam_mode_radio': 'РЕЖИМ ВЕБ-КАМЕРЫ',
		'webcam_resolution_dropdown': 'РАЗРЕШЕНИЕ ВЕБ-КАМЕРЫ',
		'webcam_fps_slider': 'ЧАСТОТА КАДРОВ ВЕБ-КАМЕРЫ'
	}
}


def get(key : str) -> Optional[str]:
	if '.' in key:
		section, name = key.split('.')
		if section in WORDING and name in WORDING[section]:
			return WORDING[section][name]
	if key in WORDING:
		return WORDING[key]
	return None
