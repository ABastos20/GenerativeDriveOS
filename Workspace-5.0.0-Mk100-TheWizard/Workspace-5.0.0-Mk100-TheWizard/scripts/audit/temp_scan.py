import os
import ast

def get_complexity(node):
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.Assert, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.AsyncFor, ast.AsyncFunctionDef)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None
    
    loc = len([line for line in content.splitlines() if line.strip()])
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None

    classes = []
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            complexity = get_complexity(node)
            if len(methods) > 20 or complexity > 15:
                classes.append((node.name, len(methods), complexity))
        
        if isinstance(node, ast.FunctionDef):
            # approximate function LOC by line difference
            if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                func_loc = node.end_lineno - node.lineno
                if func_loc > 120:
                    functions.append((node.name, func_loc))

    return loc, classes, functions

print("Scanning for violations (Task 5 Verification)...")
print("-" * 60)

EXCLUSIONS = ["docs", "tests", "migrations", "vendor", ".git", "__pycache__"]

for root, dirs, files in os.walk("."):
    # Exclusion logic
    dirs[:] = [d for d in dirs if d not in EXCLUSIONS]
    
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            # Skip tests by filename too
            if "test_" in file or "_test" in file:
                continue
                
            result = analyze_file(path)
            if result:
                loc, classes, functions = result
                
                violations = []
                if loc > 800:
                    violations.append(f"FILE LOC: {loc} > 800")
                
                for cls_name, method_count, complexity in classes:
                    if method_count > 20:
                        violations.append(f"CLASS METHODS: {cls_name} has {method_count} > 20")
                    if complexity > 15:
                        violations.append(f"CLASS COMPLEXITY: {cls_name} has {complexity} > 15")
                
                for func_name, func_loc in functions:
                    violations.append(f"FUNC LOC: {func_name} has {func_loc} > 120")
                
                if violations:
                    print(f"\n📄 {path}")
                    for v in violations:
                        print(f"  ❌ {v}")

print("-" * 60)
print("Scan complete.")
