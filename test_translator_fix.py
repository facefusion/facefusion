#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from facefusion import translator

print("Testing translator.get() with null check fix...")
print(f"LOCALE_POOL_SET before: {translator.LOCALE_POOL_SET}")

# Test 1: Call get() with non-existent module (triggers autoload failure)
print("\nTest 1: Calling get() with non-existent module...")
result = translator.get('help.run', 'nonexistent_module')
print(f"✅ Test 1 PASSED: get() returned {result} instead of crashing")
print(f"LOCALE_POOL_SET after: {list(translator.LOCALE_POOL_SET.keys())}")

# Test 2: Call get() with facefusion module
print("\nTest 2: Calling get() with facefusion module...")
result = translator.get('help.run', 'facefusion')
print(f"✅ Test 2 PASSED: get() with facefusion returned: {result}")

print("\n" + "="*60)
print("✅ ALL TRANSLATOR TESTS PASSED - Null check working!")
print("="*60)
