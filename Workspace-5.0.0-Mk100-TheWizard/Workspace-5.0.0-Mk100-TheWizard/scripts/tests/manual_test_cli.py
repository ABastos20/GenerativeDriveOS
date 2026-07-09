
import subprocess
import os

def test_cmd(cmd_list):
    print(f"Testing: {' '.join(cmd_list)}")
    try:
        env = os.environ.copy()
        env["CI"] = "true"
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
            env=env
        )
        print(f"Return Code: {result.returncode}")
        print(f"Stdout: {result.stdout[:200]}")
        print(f"Stderr: {result.stderr[:200]}")
    except Exception as e:
        print(f"Error: {e}")

print("--- Codex Variations ---")
test_cmd(["codex", "hello"])
test_cmd(["codex", "ask", "hello"])
test_cmd(["codex", "query", "hello"])

print("\n--- Claude Variations ---")
test_cmd(["claude", "hello"])
test_cmd(["claude", "ask", "hello"])
