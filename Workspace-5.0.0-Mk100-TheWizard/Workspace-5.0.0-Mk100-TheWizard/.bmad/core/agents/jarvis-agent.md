# JARVIS Agent Activation

This agent is designed to orchestrate multiple API and local LLM integrations for your self-grown assistant/advisor system.

## Activation Steps
1. Load integration config from `.bmad/integrations.yaml`.
2. Initialize API and LLM modules as defined in config.
3. Start orchestration and listen for user commands.
4. For every user/assistant turn, LOG the message into Jarvis via the MCP server:
   - Endpoint: `POST /mcp/log_message`
   - JSON body:
     - `agent`: agent identifier (e.g., `jarvis-agent`, `codex-dev`, `claude-dev`, `gemini-dev`)
     - `role`: `"user"` or `"assistant"`
     - `content`: full message text
     - `conversation_id`: UUID for this session (omit on first call; reuse value returned by server on subsequent calls)

## Example Integrations
- OpenAI API
- Local LLM (e.g., llama.cpp, GPT4All)
- Custom REST endpoints

---

## Implementation Stub (Phase0)

<!-- TODO: Implement orchestration logic below -->
# Pseudocode:
# 1. Parse integrations.yaml
# 2. For each LLM/API, initialize connection
# 3. Set up command listener for user queries
# 4. Route queries to appropriate agent/module
# 5. Log all actions for reproducibility

# Next: Fill in orchestration routines for each integration type
