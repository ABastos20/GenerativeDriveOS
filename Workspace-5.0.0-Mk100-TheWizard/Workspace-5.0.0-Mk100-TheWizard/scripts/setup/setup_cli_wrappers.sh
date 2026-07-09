#!/usr/bin/env bash
# Create CLI wrapper scripts for LLM tools in container

set -euo pipefail

echo "🔧 Setting up LLM CLI wrappers (container-local)..."

# Claude CLI wrapper (prefers npm CLI, falls back to Python SDK)
cat > /usr/local/bin/claude-cli <<'EOF'
#!/usr/bin/env python3
"""Claude CLI wrapper.

Order of preference:
1. Use global `claude` npm CLI if available and succeeds.
2. Fallback to Anthropic Python SDK.
"""
import os
import sys
import subprocess
import json
import urllib.request

def _run_npm_cli(args: list[str]) -> bool:
    """Try to run the npm `claude` CLI. Return True on success."""
    try:
        completed = subprocess.run(
            ["claude"] + args,
            check=False,
        )
        return completed.returncode == 0
    except FileNotFoundError:
        return False


def _log_to_jarvis(agent: str, role: str, content: str) -> None:
    """Best-effort log to Jarvis MCP server; ignore failures."""
    try:
        body = json.dumps(
            {
                "agent": agent,
                "role": role,
                "content": content,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8001/mcp/log_message",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.0)
    except Exception:
        # Logging must never break the CLI path
        pass

def main():
    # Parse simple args: claude-cli "prompt text"
    if len(sys.argv) < 2:
        print("Usage: claude-cli 'your prompt here'", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Log user prompt to Jarvis (best-effort)
    _log_to_jarvis(agent="claude-cli", role="user", content=prompt)

    # Prefer npm CLI if present and succeeds
    if _run_npm_cli(sys.argv[1:]):
        return

    # Fallback to Python SDK (uses Jarvis-specific env alias)
    from anthropic import Anthropic  # type: ignore[import]

    api_key = os.environ.get("JARVIS_ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: JARVIS_ANTHROPIC_API_KEY not set (and npm `claude` CLI failed)", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = message.content[0].text
    print(answer_text)

    # Log assistant answer to Jarvis (best-effort)
    _log_to_jarvis(agent="claude-cli", role="assistant", content=answer_text)

if __name__ == "__main__":
    main()
EOF

# Gemini CLI wrapper (prefers npm CLI, falls back to Python SDK)
cat > /usr/local/bin/gemini-cli <<'EOF'
#!/usr/bin/env python3
"""Gemini CLI wrapper.

Order of preference:
1. Use global `gemini` npm CLI if available and succeeds.
2. Fallback to google-generativeai Python SDK.
"""
import os
import sys
import subprocess
import json
import urllib.request

def _run_npm_cli(args: list[str]) -> bool:
    """Try to run the npm `gemini` CLI. Return True on success."""
    try:
        completed = subprocess.run(
            ["gemini"] + args,
            check=False,
        )
        return completed.returncode == 0
    except FileNotFoundError:
        return False


def _log_to_jarvis(agent: str, role: str, content: str) -> None:
    """Best-effort log to Jarvis MCP server; ignore failures."""
    try:
        body = json.dumps(
            {
                "agent": agent,
                "role": role,
                "content": content,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8001/mcp/log_message",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.0)
    except Exception:
        # Logging must never break the CLI path
        pass

def main():
    if len(sys.argv) < 2:
        print("Usage: gemini-cli 'your prompt here'", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Log user prompt to Jarvis (best-effort)
    _log_to_jarvis(agent="gemini-cli", role="user", content=prompt)

    # Prefer npm CLI if present and succeeds
    if _run_npm_cli(sys.argv[1:]):
        return

    # Fallback to Python SDK (uses Jarvis-specific env aliases)
    import google.generativeai as genai  # type: ignore[import]

    api_key = os.environ.get("JARVIS_GOOGLE_API_KEY") or os.environ.get("JARVIS_GOOGLE_GENAI_API_KEY")
    if not api_key:
        print(
            "Error: JARVIS_GOOGLE_API_KEY or JARVIS_GOOGLE_GENAI_API_KEY not set "
            "(and npm `gemini` CLI failed)",
            file=sys.stderr,
        )
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5")  # Nov 2025: Latest Gemini
    response = model.generate_content(prompt)

    answer_text = response.text
    print(answer_text)

    # Log assistant answer to Jarvis (best-effort)
    _log_to_jarvis(agent="gemini-cli", role="assistant", content=answer_text)

if __name__ == "__main__":
    main()
EOF

# OpenAI/Codex CLI wrapper (prefers npm CLI, falls back to Python SDK)
cat > /usr/local/bin/codex-cli <<'EOF'
#!/usr/bin/env python3
"""OpenAI/Codex CLI wrapper.

Order of preference:
1. Use global `codex` npm CLI if available and succeeds.
2. Fallback to OpenAI Python SDK.
"""
import os
import sys
import subprocess
import json
import urllib.request

def _run_npm_cli(args: list[str]) -> bool:
    """Try to run the npm `codex` CLI. Return True on success."""
    try:
        completed = subprocess.run(
            ["codex"] + args,
            check=False,
        )
        return completed.returncode == 0
    except FileNotFoundError:
        return False


def _log_to_jarvis(agent: str, role: str, content: str) -> None:
    """Best-effort log to Jarvis MCP server; ignore failures."""
    try:
        body = json.dumps(
            {
                "agent": agent,
                "role": role,
                "content": content,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8001/mcp/log_message",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.0)
    except Exception:
        # Logging must never break the CLI path
        pass

def main():
    if len(sys.argv) < 2:
        print("Usage: codex-cli 'your prompt here'", file=sys.stderr)
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Log user prompt to Jarvis (best-effort)
    _log_to_jarvis(agent="codex-cli", role="user", content=prompt)

    # Prefer npm CLI if present and succeeds
    if _run_npm_cli(sys.argv[1:]):
        return

    # Fallback to Python SDK (uses Jarvis-specific env alias)
    from openai import OpenAI  # type: ignore[import]

    api_key = os.environ.get("JARVIS_OPENAI_API_KEY")
    if not api_key:
        print("Error: JARVIS_OPENAI_API_KEY not set (and npm `codex` CLI failed)", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-5.1",  # Nov 2025: Latest GPT model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )

    answer_text = response.choices[0].message.content
    print(answer_text)

    # Log assistant answer to Jarvis (best-effort)
    _log_to_jarvis(agent="codex-cli", role="assistant", content=answer_text)

if __name__ == "__main__":
    main()
EOF

# Make all wrappers executable
chmod +x /usr/local/bin/claude-cli /usr/local/bin/gemini-cli /usr/local/bin/codex-cli

echo "✅ CLI wrappers installed (container):"
echo "   - claude-cli  (Anthropic Claude, Python SDK)"
echo "   - gemini-cli  (Google Gemini, Python SDK)"
echo "   - codex-cli   (OpenAI GPT, Python SDK)"
echo ""
echo "ℹ️  Set API keys in .env to use these tools"
