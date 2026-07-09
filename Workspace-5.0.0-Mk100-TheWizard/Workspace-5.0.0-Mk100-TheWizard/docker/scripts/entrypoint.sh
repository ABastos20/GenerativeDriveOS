#!/usr/bin/env bash
set -euo pipefail

HOST_UID=${HOST_UID:-1000}
HOST_GID=${HOST_GID:-1000}
APP_USER=jarvis

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  groupadd -g "${HOST_GID}" "${APP_USER}" >/dev/null 2>&1 || true
  useradd -u "${HOST_UID}" -g "${HOST_GID}" -m "${APP_USER}" >/dev/null 2>&1 || true
fi

mkdir -p /workspace/.jarvis
chown -R "${APP_USER}:${HOST_GID}" /workspace/.jarvis

# Ensure application user has a writable cache directory for models (e.g. sentence-transformers)
mkdir -p "/home/${APP_USER}/.cache"
chown -R "${APP_USER}:${HOST_GID}" "/home/${APP_USER}/.cache"

# Ensure CLI config directories mounted from host are writable by the app user
for cli_dir in ".claude" ".gemini" ".codex"; do
  if [ -d "/home/${APP_USER}/${cli_dir}" ]; then
    chown -R "${APP_USER}:${HOST_GID}" "/home/${APP_USER}/${cli_dir}" || true
  fi
done

exec gosu "${APP_USER}" "$@"
