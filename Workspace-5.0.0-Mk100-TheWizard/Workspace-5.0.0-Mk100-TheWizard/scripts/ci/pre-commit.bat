@echo off
echo 🔍 Running Jarvis Code Quality Linter...
python scripts\lint_check.py src

if %errorlevel% neq 0 (
    echo ❌ Lint check failed. Please fix violations before committing.
    exit /b 1
)

echo ✅ Lint check passed.
exit /b 0
