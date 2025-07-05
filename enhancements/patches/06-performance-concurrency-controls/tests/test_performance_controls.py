"""
Tests for Performance & Concurrency Controls override modules.
"""

import importlib

def test_execution_thread_count_override():
    mod = importlib.import_module('facefusion.uis.components.execution_thread_count')
    assert 'PerformanceThreadCountPanel' in dir(mod)

def test_execution_queue_count_override():
    mod = importlib.import_module('facefusion.uis.components.execution_queue_count')
    assert 'PerformanceQueueCountPanel' in dir(mod)

def test_common_options_override():
    mod = importlib.import_module('facefusion.uis.components.common_options')
    assert 'PerformanceCommonOptionsPanel' in dir(mod)

def test_process_manager_override():
    mod = importlib.import_module('facefusion.process_manager')
    assert 'PerformanceProcessManager' in dir(mod)
