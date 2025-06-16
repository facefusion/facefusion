import tempfile
from argparse import ArgumentParser, HelpFormatter

import facefusion.choices
from facefusion import config, metadata, state_manager, wording
from facefusion.common_helper import create_float_metavar, create_int_metavar, get_first, get_last
from facefusion.execution import get_available_execution_providers
from facefusion.ffmpeg import get_available_encoder_set
from facefusion.filesystem import get_file_name, resolve_file_paths
from facefusion.jobs import job_store
from facefusion.processors.core import get_processors_modules


def create_help_formatter_small(prog : str) -> HelpFormatter:
	return HelpFormatter(prog, max_help_position = 50)


def create_help_formatter_large(prog : str) -> HelpFormatter:
	return HelpFormatter(prog, max_help_position = 300)


def create_config_path_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('--config-path', help = wording.get('help.config_path'), default = 'facefusion.ini')
	job_store.register_job_keys([ 'config_path' ])
	apply_config_path(program)
	return program


def create_temp_path_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('--temp-path', help = wording.get('help.temp_path'), default = config.get_str_value('paths', 'temp_path', tempfile.gettempdir()))
	job_store.register_job_keys([ 'temp_path' ])
	return program


def create_jobs_path_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('--jobs-path', help = wording.get('help.jobs_path'), default = config.get_str_value('paths', 'jobs_path', '.jobs'))
	job_store.register_job_keys([ 'jobs_path' ])
	return program


def create_source_paths_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('-s', '--source-paths', help = wording.get('help.source_paths'), default = config.get_str_list('paths', 'source_paths'), nargs = '+')
	job_store.register_step_keys([ 'source_paths' ])
	return program


def create_target_path_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('-t', '--target-path', help = wording.get('help.target_path'), default = config.get_str_value('paths', 'target_path'))
	job_store.register_step_keys([ 'target_path' ])
	return program


def create_output_path_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_paths = program.add_argument_group('paths')
	group_paths.add_argument('-o', '--output-path', help = wording.get('help.output_path'), default = config.get_str_value('paths', 'output_path'))
	job_store.register_step_keys([ 'output_path' ])
	return program


def create_source_pattern_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_patterns = program.add_argument_group('patterns')
	group_patterns.add_argument('-s', '--source-pattern', help = wording.get('help.source_pattern'), default = config.get_str_value('patterns', 'source_pattern'))
	job_store.register_job_keys([ 'source_pattern' ])
	return program


def create_target_pattern_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_patterns = program.add_argument_group('patterns')
	group_patterns.add_argument('-t', '--target-pattern', help = wording.get('help.target_pattern'), default = config.get_str_value('patterns', 'target_pattern'))
	job_store.register_job_keys([ 'target_pattern' ])
	return program


def create_output_pattern_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_patterns = program.add_argument_group('patterns')
	group_patterns.add_argument('-o', '--output-pattern', help = wording.get('help.output_pattern'), default = config.get_str_value('patterns', 'output_pattern'))
	job_store.register_job_keys([ 'output_pattern' ])
	return program


def create_face_detector_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_face_detector = program.add_argument_group('face detector')
	group_face_detector.add_argument('--face-detector-model', help = wording.get('help.face_detector_model'), default = config.get_str_value('face_detector', 'face_detector_model', 'yolo_face'), choices = facefusion.choices.face_detector_models)
	known_args, _ = program.parse_known_args()
	face_detector_size_choices = facefusion.choices.face_detector_set.get(known_args.face_detector_model)
	group_face_detector.add_argument('--face-detector-size', help = wording.get('help.face_detector_size'), default = config.get_str_value('face_detector', 'face_detector_size', get_last(face_detector_size_choices)), choices = face_detector_size_choices)
	group_face_detector.add_argument('--face-detector-angles', help = wording.get('help.face_detector_angles'), type = int, default = config.get_int_list('face_detector', 'face_detector_angles', '0'), choices = facefusion.choices.face_detector_angles, nargs = '+', metavar = 'FACE_DETECTOR_ANGLES')
	group_face_detector.add_argument('--face-detector-score', help = wording.get('help.face_detector_score'), type = float, default = config.get_float_value('face_detector', 'face_detector_score', '0.5'), choices = facefusion.choices.face_detector_score_range, metavar = create_float_metavar(facefusion.choices.face_detector_score_range))
	job_store.register_step_keys([ 'face_detector_model', 'face_detector_angles', 'face_detector_size', 'face_detector_score' ])
	return program


def create_face_landmarker_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_face_landmarker = program.add_argument_group('face landmarker')
	group_face_landmarker.add_argument('--face-landmarker-model', help = wording.get('help.face_landmarker_model'), default = config.get_str_value('face_landmarker', 'face_landmarker_model', '2dfan4'), choices = facefusion.choices.face_landmarker_models)
	group_face_landmarker.add_argument('--face-landmarker-score', help = wording.get('help.face_landmarker_score'), type = float, default = config.get_float_value('face_landmarker', 'face_landmarker_score', '0.5'), choices = facefusion.choices.face_landmarker_score_range, metavar = create_float_metavar(facefusion.choices.face_landmarker_score_range))
	job_store.register_step_keys([ 'face_landmarker_model', 'face_landmarker_score' ])
	return program


def create_face_selector_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_face_selector = program.add_argument_group('face selector')
	group_face_selector.add_argument('--face-selector-mode', help = wording.get('help.face_selector_mode'), default = config.get_str_value('face_selector', 'face_selector_mode', 'reference'), choices = facefusion.choices.face_selector_modes)
	group_face_selector.add_argument('--face-selector-order', help = wording.get('help.face_selector_order'), default = config.get_str_value('face_selector', 'face_selector_order', 'large-small'), choices = facefusion.choices.face_selector_orders)
	group_face_selector.add_argument('--face-selector-age-start', help = wording.get('help.face_selector_age_start'), type = int, default = config.get_int_value('face_selector', 'face_selector_age_start'), choices = facefusion.choices.face_selector_age_range, metavar = create_int_metavar(facefusion.choices.face_selector_age_range))
	group_face_selector.add_argument('--face-selector-age-end', help = wording.get('help.face_selector_age_end'), type = int, default = config.get_int_value('face_selector', 'face_selector_age_end'), choices = facefusion.choices.face_selector_age_range, metavar = create_int_metavar(facefusion.choices.face_selector_age_range))
	group_face_selector.add_argument('--face-selector-gender', help = wording.get('help.face_selector_gender'), default = config.get_str_value('face_selector', 'face_selector_gender'), choices = facefusion.choices.face_selector_genders)
	group_face_selector.add_argument('--face-selector-race', help = wording.get('help.face_selector_race'), default = config.get_str_value('face_selector', 'face_selector_race'), choices = facefusion.choices.face_selector_races)
	group_face_selector.add_argument('--reference-face-position', help = wording.get('help.reference_face_position'), type = int, default = config.get_int_value('face_selector', 'reference_face_position', '0'))
	group_face_selector.add_argument('--reference-face-distance', help = wording.get('help.reference_face_distance'), type = float, default = config.get_float_value('face_selector', 'reference_face_distance', '0.3'), choices = facefusion.choices.reference_face_distance_range, metavar = create_float_metavar(facefusion.choices.reference_face_distance_range))
	group_face_selector.add_argument('--reference-frame-number', help = wording.get('help.reference_frame_number'), type = int, default = config.get_int_value('face_selector', 'reference_frame_number', '0'))
	job_store.register_step_keys([ 'face_selector_mode', 'face_selector_order', 'face_selector_gender', 'face_selector_race', 'face_selector_age_start', 'face_selector_age_end', 'reference_face_position', 'reference_face_distance', 'reference_frame_number' ])
	return program


def create_face_masker_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_face_masker = program.add_argument_group('face masker')
	group_face_masker.add_argument('--face-occluder-model', help = wording.get('help.face_occluder_model'), default = config.get_str_value('face_masker', 'face_occluder_model', 'xseg_1'), choices = facefusion.choices.face_occluder_models)
	group_face_masker.add_argument('--face-parser-model', help = wording.get('help.face_parser_model'), default = config.get_str_value('face_masker', 'face_parser_model', 'bisenet_resnet_34'), choices = facefusion.choices.face_parser_models)
	group_face_masker.add_argument('--face-mask-types', help = wording.get('help.face_mask_types').format(choices = ', '.join(facefusion.choices.face_mask_types)), default = config.get_str_list('face_masker', 'face_mask_types', 'box'), choices = facefusion.choices.face_mask_types, nargs = '+', metavar = 'FACE_MASK_TYPES')
	group_face_masker.add_argument('--face-mask-areas', help = wording.get('help.face_mask_areas').format(choices = ', '.join(facefusion.choices.face_mask_areas)), default = config.get_str_list('face_masker', 'face_mask_areas', ' '.join(facefusion.choices.face_mask_areas)), choices = facefusion.choices.face_mask_areas, nargs = '+', metavar = 'FACE_MASK_AREAS')
	group_face_masker.add_argument('--face-mask-regions', help = wording.get('help.face_mask_regions').format(choices = ', '.join(facefusion.choices.face_mask_regions)), default = config.get_str_list('face_masker', 'face_mask_regions', ' '.join(facefusion.choices.face_mask_regions)), choices = facefusion.choices.face_mask_regions, nargs = '+', metavar = 'FACE_MASK_REGIONS')
	group_face_masker.add_argument('--face-mask-blur', help = wording.get('help.face_mask_blur'), type = float, default = config.get_float_value('face_masker', 'face_mask_blur', '0.3'), choices = facefusion.choices.face_mask_blur_range, metavar = create_float_metavar(facefusion.choices.face_mask_blur_range))
	group_face_masker.add_argument('--face-mask-padding', help = wording.get('help.face_mask_padding'), type = int, default = config.get_int_list('face_masker', 'face_mask_padding', '0 0 0 0'), nargs = '+')
	job_store.register_step_keys([ 'face_occluder_model', 'face_parser_model', 'face_mask_types', 'face_mask_areas', 'face_mask_regions', 'face_mask_blur', 'face_mask_padding' ])
	return program


def create_frame_extraction_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_frame_extraction = program.add_argument_group('frame extraction')
	group_frame_extraction.add_argument('--trim-frame-start', help = wording.get('help.trim_frame_start'), type = int, default = facefusion.config.get_int_value('frame_extraction', 'trim_frame_start'))
	group_frame_extraction.add_argument('--trim-frame-end', help = wording.get('help.trim_frame_end'), type = int, default = facefusion.config.get_int_value('frame_extraction', 'trim_frame_end'))
	group_frame_extraction.add_argument('--temp-frame-format', help = wording.get('help.temp_frame_format'), default = config.get_str_value('frame_extraction', 'temp_frame_format', 'png'), choices = facefusion.choices.temp_frame_formats)
	group_frame_extraction.add_argument('--keep-temp', help = wording.get('help.keep_temp'), action = 'store_true', default = config.get_bool_value('frame_extraction', 'keep_temp'))
	job_store.register_step_keys([ 'trim_frame_start', 'trim_frame_end', 'temp_frame_format', 'keep_temp' ])
	return program


def create_output_creation_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	available_encoder_set = get_available_encoder_set()
	group_output_creation = program.add_argument_group('output creation')
	group_output_creation.add_argument('--output-image-quality', help = wording.get('help.output_image_quality'), type = int, default = config.get_int_value('output_creation', 'output_image_quality', '80'), choices = facefusion.choices.output_image_quality_range, metavar = create_int_metavar(facefusion.choices.output_image_quality_range))
	group_output_creation.add_argument('--output-image-resolution', help = wording.get('help.output_image_resolution'), default = config.get_str_value('output_creation', 'output_image_resolution'))
	group_output_creation.add_argument('--output-audio-encoder', help = wording.get('help.output_audio_encoder'), default = config.get_str_value('output_creation', 'output_audio_encoder', get_first(available_encoder_set.get('audio'))), choices = available_encoder_set.get('audio'))
	group_output_creation.add_argument('--output-audio-quality', help = wording.get('help.output_audio_quality'), type = int, default = config.get_int_value('output_creation', 'output_audio_quality', '80'), choices = facefusion.choices.output_audio_quality_range, metavar = create_int_metavar(facefusion.choices.output_audio_quality_range))
	group_output_creation.add_argument('--output-audio-volume', help = wording.get('help.output_audio_volume'), type = int, default = config.get_int_value('output_creation', 'output_audio_volume', '100'), choices = facefusion.choices.output_audio_volume_range, metavar = create_int_metavar(facefusion.choices.output_audio_volume_range))
	group_output_creation.add_argument('--output-video-encoder', help = wording.get('help.output_video_encoder'), default = config.get_str_value('output_creation', 'output_video_encoder', get_first(available_encoder_set.get('video'))), choices = available_encoder_set.get('video'))
	group_output_creation.add_argument('--output-video-preset', help = wording.get('help.output_video_preset'), default = config.get_str_value('output_creation', 'output_video_preset', 'veryfast'), choices = facefusion.choices.output_video_presets)
	group_output_creation.add_argument('--output-video-quality', help = wording.get('help.output_video_quality'), type = int, default = config.get_int_value('output_creation', 'output_video_quality', '80'), choices = facefusion.choices.output_video_quality_range, metavar = create_int_metavar(facefusion.choices.output_video_quality_range))
	group_output_creation.add_argument('--output-video-resolution', help = wording.get('help.output_video_resolution'), default = config.get_str_value('output_creation', 'output_video_resolution'))
	group_output_creation.add_argument('--output-video-fps', help = wording.get('help.output_video_fps'), type = float, default = config.get_str_value('output_creation', 'output_video_fps'))
	job_store.register_step_keys([ 'output_image_quality', 'output_image_resolution', 'output_audio_encoder', 'output_audio_quality', 'output_audio_volume', 'output_video_encoder', 'output_video_preset', 'output_video_quality', 'output_video_resolution', 'output_video_fps' ])
	return program


def create_processors_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/processors/modules') ]
	group_processors = program.add_argument_group('processors')
	group_processors.add_argument('--processors', help = wording.get('help.processors').format(choices = ', '.join(available_processors)), default = config.get_str_list('processors', 'processors', 'face_swapper'), nargs = '+')
	job_store.register_step_keys([ 'processors' ])
	for processor_module in get_processors_modules(available_processors):
		processor_module.register_args(program)
	return program


def create_uis_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	available_ui_layouts = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/uis/layouts') ]
	group_uis = program.add_argument_group('uis')
	group_uis.add_argument('--open-browser', help = wording.get('help.open_browser'), action = 'store_true', default = config.get_bool_value('uis', 'open_browser'))
	group_uis.add_argument('--ui-layouts', help = wording.get('help.ui_layouts').format(choices = ', '.join(available_ui_layouts)), default = config.get_str_list('uis', 'ui_layouts', 'default'), nargs = '+')
	group_uis.add_argument('--ui-workflow', help = wording.get('help.ui_workflow'), default = config.get_str_value('uis', 'ui_workflow', 'instant_runner'), choices = facefusion.choices.ui_workflows)
	return program


def create_download_providers_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_download = program.add_argument_group('download')
	group_download.add_argument('--download-providers', help = wording.get('help.download_providers').format(choices = ', '.join(facefusion.choices.download_providers)), default = config.get_str_list('download', 'download_providers', ' '.join(facefusion.choices.download_providers)), choices = facefusion.choices.download_providers, nargs = '+', metavar = 'DOWNLOAD_PROVIDERS')
	job_store.register_job_keys([ 'download_providers' ])
	return program


def create_download_scope_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_download = program.add_argument_group('download')
	group_download.add_argument('--download-scope', help = wording.get('help.download_scope'), default = config.get_str_value('download', 'download_scope', 'lite'), choices = facefusion.choices.download_scopes)
	job_store.register_job_keys([ 'download_scope' ])
	return program


def create_benchmark_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_benchmark = program.add_argument_group('benchmark')
	group_benchmark.add_argument('--benchmark-resolutions', help = wording.get('help.benchmark_resolutions'), default = config.get_str_list('benchmark', 'benchmark_resolutions', get_first(facefusion.choices.benchmark_resolutions)), choices = facefusion.choices.benchmark_resolutions, nargs = '+')
	group_benchmark.add_argument('--benchmark-cycle-count', help = wording.get('help.benchmark_cycle_count'), type = int, default = config.get_int_value('benchmark', 'benchmark_cycle_count', '5'), choices = facefusion.choices.benchmark_cycle_count_range)
	return program


def create_execution_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	available_execution_providers = get_available_execution_providers()
	group_execution = program.add_argument_group('execution')
	group_execution.add_argument('--execution-device-id', help = wording.get('help.execution_device_id'), default = config.get_str_value('execution', 'execution_device_id', '0'))
	group_execution.add_argument('--execution-providers', help = wording.get('help.execution_providers').format(choices = ', '.join(available_execution_providers)), default = config.get_str_list('execution', 'execution_providers', get_first(available_execution_providers)), choices = available_execution_providers, nargs = '+', metavar = 'EXECUTION_PROVIDERS')
	group_execution.add_argument('--execution-thread-count', help = wording.get('help.execution_thread_count'), type = int, default = config.get_int_value('execution', 'execution_thread_count', '4'), choices = facefusion.choices.execution_thread_count_range, metavar = create_int_metavar(facefusion.choices.execution_thread_count_range))
	group_execution.add_argument('--execution-queue-count', help = wording.get('help.execution_queue_count'), type = int, default = config.get_int_value('execution', 'execution_queue_count', '1'), choices = facefusion.choices.execution_queue_count_range, metavar = create_int_metavar(facefusion.choices.execution_queue_count_range))
	job_store.register_job_keys([ 'execution_device_id', 'execution_providers', 'execution_thread_count', 'execution_queue_count' ])
	return program


def create_memory_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_memory = program.add_argument_group('memory')
	group_memory.add_argument('--video-memory-strategy', help = wording.get('help.video_memory_strategy'), default = config.get_str_value('memory', 'video_memory_strategy', 'strict'), choices = facefusion.choices.video_memory_strategies)
	group_memory.add_argument('--system-memory-limit', help = wording.get('help.system_memory_limit'), type = int, default = config.get_int_value('memory', 'system_memory_limit', '0'), choices = facefusion.choices.system_memory_limit_range, metavar = create_int_metavar(facefusion.choices.system_memory_limit_range))
	job_store.register_job_keys([ 'video_memory_strategy', 'system_memory_limit' ])
	return program


def create_log_level_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_misc = program.add_argument_group('misc')
	group_misc.add_argument('--log-level', help = wording.get('help.log_level'), default = config.get_str_value('misc', 'log_level', 'info'), choices = facefusion.choices.log_levels)
	job_store.register_job_keys([ 'log_level' ])
	return program


def create_halt_on_error_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	group_misc = program.add_argument_group('misc')
	group_misc.add_argument('--halt-on-error', help = wording.get('help.halt_on_error'), action = 'store_true', default = config.get_bool_value('misc', 'halt_on_error'))
	job_store.register_job_keys([ 'halt_on_error' ])
	return program


def create_job_id_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	program.add_argument('job_id', help = wording.get('help.job_id'))
	job_store.register_job_keys([ 'job_id' ])
	return program


def create_job_status_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	program.add_argument('job_status', help = wording.get('help.job_status'), choices = facefusion.choices.job_statuses)
	return program


def create_step_index_program() -> ArgumentParser:
	program = ArgumentParser(add_help = False)
	program.add_argument('step_index', help = wording.get('help.step_index'), type = int)
	return program


def collect_step_program() -> ArgumentParser:
	return ArgumentParser(parents = [ create_face_detector_program(), create_face_landmarker_program(), create_face_selector_program(), create_face_masker_program(), create_frame_extraction_program(), create_output_creation_program(), create_processors_program() ], add_help = False)


def collect_job_program() -> ArgumentParser:
	return ArgumentParser(parents = [ create_execution_program(), create_download_providers_program(), create_memory_program(), create_log_level_program() ], add_help = False)


def create_program() -> ArgumentParser:
	program = ArgumentParser(formatter_class = create_help_formatter_large, add_help = False)
	program._positionals.title = 'commands'
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	sub_program = program.add_subparsers(dest = 'command')
	# general
	sub_program.add_parser('run', help = wording.get('help.run'), parents = [ create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), create_source_paths_program(), create_target_path_program(), create_output_path_program(), collect_step_program(), create_uis_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('headless-run', help = wording.get('help.headless_run'), parents = [ create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), create_source_paths_program(), create_target_path_program(), create_output_path_program(), collect_step_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('batch-run', help = wording.get('help.batch_run'), parents = [ create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), create_source_pattern_program(), create_target_pattern_program(), create_output_pattern_program(), collect_step_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('force-download', help = wording.get('help.force_download'), parents = [ create_download_providers_program(), create_download_scope_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('benchmark', help = wording.get('help.benchmark'), parents = [ create_temp_path_program(), collect_step_program(), create_benchmark_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	# job manager
	sub_program.add_parser('job-list', help = wording.get('help.job_list'), parents = [ create_job_status_program(), create_jobs_path_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-create', help = wording.get('help.job_create'), parents = [ create_job_id_program(), create_jobs_path_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-submit', help = wording.get('help.job_submit'), parents = [ create_job_id_program(), create_jobs_path_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-submit-all', help = wording.get('help.job_submit_all'), parents = [ create_jobs_path_program(), create_log_level_program(), create_halt_on_error_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-delete', help = wording.get('help.job_delete'), parents = [ create_job_id_program(), create_jobs_path_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-delete-all', help = wording.get('help.job_delete_all'), parents = [ create_jobs_path_program(), create_log_level_program(), create_halt_on_error_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-add-step', help = wording.get('help.job_add_step'), parents = [ create_job_id_program(), create_config_path_program(), create_jobs_path_program(), create_source_paths_program(), create_target_path_program(), create_output_path_program(), collect_step_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-remix-step', help = wording.get('help.job_remix_step'), parents = [ create_job_id_program(), create_step_index_program(), create_config_path_program(), create_jobs_path_program(), create_source_paths_program(), create_output_path_program(), collect_step_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-insert-step', help = wording.get('help.job_insert_step'), parents = [ create_job_id_program(), create_step_index_program(), create_config_path_program(), create_jobs_path_program(), create_source_paths_program(), create_target_path_program(), create_output_path_program(), collect_step_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-remove-step', help = wording.get('help.job_remove_step'), parents = [ create_job_id_program(), create_step_index_program(), create_jobs_path_program(), create_log_level_program() ], formatter_class = create_help_formatter_large)
	# job runner
	sub_program.add_parser('job-run', help = wording.get('help.job_run'), parents = [ create_job_id_program(), create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-run-all', help = wording.get('help.job_run_all'), parents = [ create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), collect_job_program(), create_halt_on_error_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-retry', help = wording.get('help.job_retry'), parents = [ create_job_id_program(), create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), collect_job_program() ], formatter_class = create_help_formatter_large)
	sub_program.add_parser('job-retry-all', help = wording.get('help.job_retry_all'), parents = [ create_config_path_program(), create_temp_path_program(), create_jobs_path_program(), collect_job_program(), create_halt_on_error_program() ], formatter_class = create_help_formatter_large)
	return ArgumentParser(parents = [ program ], formatter_class = create_help_formatter_small)


def apply_config_path(program : ArgumentParser) -> None:
	known_args, _ = program.parse_known_args()
	state_manager.init_item('config_path', known_args.config_path)
