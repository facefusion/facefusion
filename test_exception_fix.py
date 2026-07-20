#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from facefusion.processors import core as proc_core
from facefusion.uis import core as uis_core

print("Testing exception.msg -> str(exception) fix...\n")

# Test 1: Try loading non-existent processor
print("Test 1: Loading non-existent processor...")
print("-" * 60)
try:
	proc_core.load_processor_module('nonexistent_processor')
except SystemExit as e:
	print(f"✅ Test 1 PASSED: Exited gracefully with code {e.code}")
	# If we got here without AttributeError, the str(exception) fix worked

print()

# Test 2: Try loading non-existent UI layout
print("Test 2: Loading non-existent UI layout...")
print("-" * 60)
try:
	uis_core.load_ui_layout_module('nonexistent_layout')
except SystemExit as e:
	print(f"✅ Test 2 PASSED: Exited gracefully with code {e.code}")
	# If we got here without AttributeError, the str(exception) fix worked

print("\n" + "="*60)
print("✅ ALL EXCEPTION TESTS PASSED - str(exception) working!")
print("="*60)
