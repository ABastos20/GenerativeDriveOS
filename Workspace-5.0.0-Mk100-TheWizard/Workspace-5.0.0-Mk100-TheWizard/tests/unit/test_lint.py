import os
import pytest
import tempfile
import json
from scripts.ci.lint_check import check_file, Violation, MAX_FILE_LOC, MAX_METHODS_PER_CLASS, MAX_FUNCTION_LOC

def create_temp_file(content):
    fd, path = tempfile.mkstemp(suffix=".py", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def test_loc_violation():
    # Create file with > 800 lines
    content = "\n".join([f"x = {i}" for i in range(MAX_FILE_LOC + 10)])
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert any(v.rule == "MAX_FILE_LOC" for v in violations)
    finally:
        os.remove(path)

def test_method_count_violation():
    methods = "\n    ".join([f"def method_{i}(self): pass" for i in range(MAX_METHODS_PER_CLASS + 5)])
    content = f"class TooManyMethods:\n    {methods}"
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert any(v.rule == "MAX_METHODS" for v in violations)
    finally:
        os.remove(path)

def test_function_loc_violation():
    body = "\n    ".join([f"x = {i}" for i in range(MAX_FUNCTION_LOC + 10)])
    content = f"def too_long_function():\n    {body}"
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert any(v.rule == "MAX_FUNC_LOC" for v in violations)
    finally:
        os.remove(path)

def test_exclusions_pragma():
    # Test File LOC Pragma
    content = "# jarvis:allow-large-file\n" + "\n".join([f"x = {i}" for i in range(MAX_FILE_LOC + 10)])
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert not any(v.rule == "MAX_FILE_LOC" for v in violations)
    finally:
        os.remove(path)

    # Test Method Count Pragma
    methods = "\n    ".join([f"def method_{i}(self): pass" for i in range(MAX_METHODS_PER_CLASS + 5)])
    content = f"# jarvis:allow-many-methods\nclass TooManyMethods:\n    {methods}"
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert not any(v.rule == "MAX_METHODS" for v in violations)
    finally:
        os.remove(path)

    # Test Function LOC Pragma
    body = "\n    ".join([f"x = {i}" for i in range(MAX_FUNCTION_LOC + 10)])
    content = f"# jarvis:allow-large-function\ndef too_long_function():\n    {body}"
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert not any(v.rule == "MAX_FUNC_LOC" for v in violations)
    finally:
        os.remove(path)

def test_complexity_pragma():
    # Create complex code: if x: if y: ... nested 20 times
    nested = "pass"
    for i in range(20):
        nested = f"if True:\n    {nested}"
    content = f"# jarvis:allow-complex\nclass Complex:\n  def complex_method(self):\n    {nested}"
    # Indentation fix
    lines = content.splitlines()
    # This is a bit hacky to generate valid python with deep nesting, 
    # but let's rely on the fact that the linter checks AST complexity.
    # Actually, let's just use a sequence of ifs which is easier to generate valid code for.
    ifs = "\n        ".join(["if True: pass" for _ in range(20)])
    content = f"# jarvis:allow-complex\nclass Complex:\n    def complex_method(self):\n        {ifs}"
    
    path = create_temp_file(content)
    try:
        violations = check_file(path)
        assert not any(v.rule == "MAX_COMPLEXITY" for v in violations)
    finally:
        os.remove(path)
