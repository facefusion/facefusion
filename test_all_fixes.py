#!/usr/bin/env python3
"""
Comprehensive test suite for import and module loading fixes.

Tests:
1. translator.py - Null check for locale_set
2. processors/core.py - exception.msg -> str(exception)
3. uis/core.py - exception.msg -> str(exception)
"""

import sys
import io
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, '.')

from facefusion import translator
from facefusion.processors import core as proc_core
from facefusion.uis import core as uis_core

def test_translator_null_check():
	"""Test translator.get() handles missing locales gracefully."""
	print("\n" + "="*70)
	print("TEST 1: translator.py - Null Check Fix")
	print("="*70)
	
	try:
		print("\n[1.1] Testing get() with non-existent module...")
		result = translator.get('help.run', 'nonexistent_module')
		
		if result is None:
			print("      ✅ PASS: Returned None instead of crashing")
			return True
		else:
			print(f"      ❌ FAIL: Expected None, got {result}")
			return False
			
	except TypeError as e:
		if "'NoneType' object is not subscriptable" in str(e):
			print(f"      ❌ FAIL: Null check didn't work: {e}")
			return False
		else:
			print(f"      ❌ FAIL: Unexpected TypeError: {e}")
			return False
			
	except Exception as e:
		print(f"      ❌ FAIL: Unexpected error: {type(e).__name__}: {e}")
		return False

def test_processor_exception_handling():
	"""Test processors/core.py handles exceptions properly."""
	print("\n" + "="*70)
	print("TEST 2: processors/core.py - exception.msg Fix")
	print("="*70)
	
	try:
		print("\n[2.1] Attempting to load non-existent processor...")
		
		# Capture stderr to avoid cluttering output
		f = io.StringIO()
		with redirect_stderr(f):
			try:
				proc_core.load_processor_module('nonexistent_processor')
			except SystemExit:
				pass
		
		error_output = f.getvalue()
		
		if "'ModuleNotFoundError' object has no attribute 'msg'" in error_output:
			print("      ❌ FAIL: exception.msg AttributeError still present")
			return False
		else:
			print("      ✅ PASS: No exception.msg AttributeError")
			return True
			
	except AttributeError as e:
		if "'msg'" in str(e):
			print(f"      ❌ FAIL: exception.msg error occurred: {e}")
			return False
		else:
			raise
			
	except Exception as e:
		print(f"      ❌ FAIL: Unexpected error: {type(e).__name__}: {e}")
		return False

def test_uis_exception_handling():
	"""Test uis/core.py handles exceptions properly."""
	print("\n" + "="*70)
	print("TEST 3: uis/core.py - exception.msg Fix")
	print("="*70)
	
	try:
		print("\n[3.1] Attempting to load non-existent UI layout...")
		
		# Capture stderr to avoid cluttering output
		f = io.StringIO()
		with redirect_stderr(f):
			try:
				uis_core.load_ui_layout_module('nonexistent_layout')
			except SystemExit:
				pass
		
		error_output = f.getvalue()
		
		if "'ModuleNotFoundError' object has no attribute 'msg'" in error_output:
			print("      ❌ FAIL: exception.msg AttributeError still present")
			return False
		else:
			print("      ✅ PASS: No exception.msg AttributeError")
			return True
			
	except AttributeError as e:
		if "'msg'" in str(e):
			print(f"      ❌ FAIL: exception.msg error occurred: {e}")
			return False
		else:
			raise
			
	except Exception as e:
		print(f"      ❌ FAIL: Unexpected error: {type(e).__name__}: {e}")
		return False

def main():
	print("\n" + "#"*70)
	print("# FaceFusion Import/Module Loading Fixes - Test Suite")
	print("#"*70)
	
	results = []
	
	# Run all tests
	results.append(("Translator Null Check", test_translator_null_check()))
	results.append(("Processors Exception Fix", test_processor_exception_handling()))
	results.append(("UIs Exception Fix", test_uis_exception_handling()))
	
	# Summary
	print("\n" + "="*70)
	print("TEST SUMMARY")
	print("="*70)
	
	passed = sum(1 for _, result in results if result)
	total = len(results)
	
	for test_name, result in results:
		status = "✅ PASS" if result else "❌ FAIL"
		print(f"{status}: {test_name}")
	
	print("\n" + "-"*70)
	if passed == total:
		print(f"✅ ALL {total} TESTS PASSED!")
		print("-"*70)
		return 0
	else:
		print(f"❌ {total - passed}/{total} TESTS FAILED")
		print("-"*70)
		return 1

if __name__ == '__main__':
	sys.exit(main())
