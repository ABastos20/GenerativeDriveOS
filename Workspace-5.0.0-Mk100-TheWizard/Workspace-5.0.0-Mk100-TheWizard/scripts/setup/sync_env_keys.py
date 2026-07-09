#!/usr/bin/env python3
"""Sync API keys from environment to .env file."""
import os
import re

ENV_FILE = "/workspace/.env"
API_KEYS = [
    "OPENROUTER_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_API_KEY",
    "OPENAI_API_KEY",
    "TOGETHER_API_KEY",
]

def read_env_file():
    """Read current .env file."""
    if not os.path.exists(ENV_FILE):
        return {}

    env_vars = {}
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def get_available_keys():
    """Get API keys from current environment."""
    available = {}
    for key in API_KEYS:
        value = os.environ.get(key)
        if value and value.strip():  # Only add non-empty keys
            available[key] = value
            print(f"✓ Found {key}: {value[:20]}...")
        else:
            print(f"✗ {key}: not set")
    return available

def update_env_file(current_env, new_keys):
    """Update .env file with new keys."""
    updated = False

    for key, value in new_keys.items():
        current_value = current_env.get(key, "")
        if not current_value or current_value.strip() == "":
            print(f"\n→ Adding {key} to .env")
            current_env[key] = value
            updated = True
        elif current_value != value:
            print(f"\n⚠️  {key} has different value in .env (keeping existing)")

    if not updated:
        print("\n✅ .env is already up to date!")
        return False

    # Write updated .env
    with open(ENV_FILE, 'r') as f:
        lines = f.readlines()

    # Update existing keys or add new ones
    updated_lines = []
    keys_written = set()

    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=', 1)[0].strip()
            if key in new_keys:
                updated_lines.append(f"{key}={new_keys[key]}\n")
                keys_written.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add any keys that weren't in the file
    for key in new_keys:
        if key not in keys_written:
            updated_lines.append(f"{key}={new_keys[key]}\n")

    with open(ENV_FILE, 'w') as f:
        f.writelines(updated_lines)

    print(f"\n✅ Updated {ENV_FILE}")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Syncing API keys from environment to .env")
    print("=" * 60)

    print("\n1. Checking current environment...")
    available_keys = get_available_keys()

    if not available_keys:
        print("\n⚠️  No API keys found in environment.")
        print("   Keys are loaded from .env, which is already the source.")
        print("   To add new keys, edit .env directly.")
    else:
        print(f"\n2. Reading current .env file...")
        current_env = read_env_file()

        print(f"\n3. Updating .env file...")
        updated = update_env_file(current_env, available_keys)

        if updated:
            print("\n✅ Done! Restart containers to use updated keys:")
            print("   docker compose -f docker/docker-compose.yml restart jarvis")
