#!/usr/bin/env bash
# Jarvis workspace aliases - source this file for quick commands
# Usage: source .bmad/aliases.sh

# Jarvis query shortcuts
alias jq='docker compose -f docker/docker-compose.yml exec jarvis jarvis query'
alias jqs='docker compose -f docker/docker-compose.yml exec jarvis jarvis query --strict-mode'

# Workspace helpers
alias jstatus='./scripts/ops/workspace_status.sh'
alias jrefresh='./scripts/bmad/bmad_refresh.sh'
alias jclean='./scripts/ops/kill_background.sh'

# Docker management
alias jlogs='docker compose -f docker/docker-compose.yml logs -f jarvis'
alias jshell='docker compose -f docker/docker-compose.yml exec jarvis bash'
alias jrestart='docker compose -f docker/docker-compose.yml restart jarvis'
alias jps='docker compose -f docker/docker-compose.yml ps'

# Development shortcuts
alias jtest='docker compose -f docker/docker-compose.yml exec jarvis pytest'
alias jcov='docker compose -f docker/docker-compose.yml exec jarvis pytest --cov=src --cov-report=term-missing'

echo "✅ Jarvis aliases loaded. Try: jq \"your question\" or jstatus"
