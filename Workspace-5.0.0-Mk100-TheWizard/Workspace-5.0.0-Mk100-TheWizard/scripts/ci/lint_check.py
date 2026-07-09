import os
import ast
import sys
import json
import argparse
from typing import List, Dict, Any, Tuple

# Default Limits
MAX_FILE_LOC = 800
MAX_METHODS_PER_CLASS = 20
MAX_FUNCTION_LOC = 120
MAX_CYCLOMATIC_COMPLEXITY = 15

# Default Exclusions
DEFAULT_EXCLUDED_DIRS = [
    "docs", "tests", "migrations", "vendor", ".git", "__pycache__", ".venv", "env", "venv"
]

class Violation:
    def __init__(self, file_path: str, rule: str, message: str, line: int = 0):
        self.file_path = file_path
        self.rule = rule
        self.message = message
        self.line = line

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file_path,
            "rule": self.rule,
            "message": self.message,
            "line": self.line
        }

def get_complexity(node: ast.AST) -> int:
    """Calculate Cyclomatic Complexity."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.Assert, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.AsyncFor, ast.AsyncFunctionDef)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def check_file(filepath: str) -> List[Violation]:
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [Violation(filepath, "READ_ERROR", str(e))]

    # Check File LOC
    lines = [line for line in content.splitlines() if line.strip()]
    loc = len(lines)
    
    # Check for file-level pragma
    if "# jarvis:allow-large-file" in content:
        pass # Allowed
    elif loc > MAX_FILE_LOC:
        violations.append(Violation(filepath, "MAX_FILE_LOC", f"File has {loc} LOC (Limit: {MAX_FILE_LOC})"))

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [Violation(filepath, "SYNTAX_ERROR", str(e), e.lineno)]

    for node in ast.walk(tree):
        # Check Class Metrics
        if isinstance(node, ast.ClassDef):
            # Check for class-level pragma (simple check in docstring or preceding comment is hard in AST, 
            # so we check file content for now or assume file-level pragma covers it. 
            # For strict method limit, we can check if the class name is in an allowed list if we wanted.)
            
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            method_count = len(methods)
            
            if method_count > MAX_METHODS_PER_CLASS:
                 # Check if file allows many methods
                if "# jarvis:allow-many-methods" not in content:
                    violations.append(Violation(filepath, "MAX_METHODS", f"Class '{node.name}' has {method_count} methods (Limit: {MAX_METHODS_PER_CLASS})", node.lineno))
            
            complexity = get_complexity(node)
            if complexity > MAX_CYCLOMATIC_COMPLEXITY:
                 if "# jarvis:allow-complex" not in content:
                    violations.append(Violation(filepath, "MAX_COMPLEXITY", f"Class '{node.name}' has complexity {complexity} (Limit: {MAX_CYCLOMATIC_COMPLEXITY})", node.lineno))

        # Check Function Metrics
        if isinstance(node, ast.FunctionDef):
            # Approximate LOC by line difference
            if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                func_loc = node.end_lineno - node.lineno
                if func_loc > MAX_FUNCTION_LOC:
                     if "# jarvis:allow-large-function" not in content:
                        violations.append(Violation(filepath, "MAX_FUNC_LOC", f"Function '{node.name}' has {func_loc} LOC (Limit: {MAX_FUNCTION_LOC})", node.lineno))

    return violations

def main():
    parser = argparse.ArgumentParser(description="Jarvis Code Quality Linter")
    parser.add_argument("paths", nargs="*", default=["src"], help="Paths to scan (default: src)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--exclude", nargs="*", default=[], help="Additional excluded directories")
    args = parser.parse_args()

    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS + args.exclude)
    all_violations = []

    for path in args.paths:
        if os.path.isfile(path):
            if path.endswith(".py"):
                all_violations.extend(check_file(path))
        else:
            for root, dirs, files in os.walk(path):
                # Modify dirs in-place to skip excluded
                dirs[:] = [d for d in dirs if d not in excluded_dirs]
                
                for file in files:
                    if file.endswith(".py"):
                        # Skip tests by filename convention as well
                        if "test_" in file or "_test" in file:
                            continue
                            
                        filepath = os.path.join(root, file)
                        all_violations.extend(check_file(filepath))

    if args.json:
        output = [v.to_dict() for v in all_violations]
        print(json.dumps(output, indent=2))
    else:
        if not all_violations:
            print("✅ No violations found.")
        else:
            print(f"❌ Found {len(all_violations)} violations:")
            for v in all_violations:
                print(f"  [{v.rule}] {v.file_path}:{v.line} - {v.message}")

    if all_violations:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
