#!/usr/bin/env python3

from common_helper import get_first, get_last

# Test various types
print("=== Testing get_first and get_last ===")

# List test
numbers = [1, 2, 3, 4, 5]
print(f"List {numbers}: first={get_first(numbers)}, last={get_last(numbers)}")

# Tuple test
colors = ("red", "green", "blue")
print(f"Tuple {colors}: first={get_first(colors)}, last={get_last(colors)}")

# String test
text = "hello"
print(f"String '{text}': first={get_first(text)}, last={get_last(text)}")

# Empty test
empty = []
print(f"Empty list: first={get_first(empty)}, last={get_last(empty)}")

print("=== All tests completed successfully ===") 