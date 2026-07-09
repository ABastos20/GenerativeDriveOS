#!/bin/bash
# Add Poetry venv to PATH in container
#
# This script adds the Poetry virtual environment's bin directory to PATH
# so you can run `jarvis` directly without `poetry run`

set -e

echo "=========================================="
echo "JARVIS CLI PATH Setup"
echo "=========================================="
echo ""

# Check if running inside container
if [ ! -f "/.dockerenv" ]; then
    echo "Error: This script must run inside the Docker container"
    echo ""
    echo "Run: docker exec -it jarvis-app bash /workspace/scripts/setup-path.sh"
    exit 1
fi

VENV_BIN="/workspace/.venv/bin"

# Check if venv exists
if [ ! -d "$VENV_BIN" ]; then
    echo "Error: Virtual environment not found at $VENV_BIN"
    echo "Run 'poetry install' first"
    exit 1
fi

# Add to ~/.bashrc if not already there
if grep -q "$VENV_BIN" ~/.bashrc 2>/dev/null; then
    echo "✓ PATH already configured in ~/.bashrc"
else
    echo "Adding $VENV_BIN to PATH in ~/.bashrc..."
    echo "" >> ~/.bashrc
    echo "# JARVIS CLI - Added by setup-path.sh" >> ~/.bashrc
    echo "export PATH=\"$VENV_BIN:\$PATH\"" >> ~/.bashrc
    echo "✓ PATH configured in ~/.bashrc"
fi

# Also export for current session
export PATH="$VENV_BIN:$PATH"

echo ""
echo "Testing jarvis command..."

if jarvis --help > /dev/null 2>&1; then
    echo "✓ jarvis command works!"
else
    echo "✗ jarvis command not found"
    echo ""
    echo "Try:"
    echo "  source ~/.bashrc"
    echo "  jarvis --help"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "You can now use 'jarvis' directly:"
echo "  jarvis --help"
echo "  jarvis health check"
echo "  jarvis analytics snapshot"
echo ""
echo "For new shell sessions, the PATH is set in ~/.bashrc"
echo ""
