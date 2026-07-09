# Persona Configuration Schema

This directory contains the Council of Ricks persona configurations.

## personas.yaml

JSON-compatible YAML file defining agent personas for multi-agent consensus voting.

### Schema

```json
{
  "personas": [
    {
      "name": "string (required)",
      "system_prompt": "string (required)",
      "weight": "float 0.0-1.0 (required)",
      "enabled": "boolean (optional, default: true)"
    }
  ]
}
```

### Field Descriptions

- **name**: Unique persona identifier (e.g., "Rickiest Rick", "Supportive Rick")
- **system_prompt**: LLM system prompt defining persona behavior and tone
- **weight**: Voting weight as decimal (0.0 to 1.0). Enabled personas **must sum to exactly 1.00** (100%)
- **enabled**: Whether persona participates in consensus voting (default: true)

### Validation Rules

1. **Weight Totals**: Enabled personas' weights must sum to 1.00 (±0.005 tolerance)
2. **At Least One Enabled**: Must have at least one enabled persona
3. **Weight Range**: Each weight must be between 0.0 and 1.0
4. **Non-Empty Fields**: name and system_prompt cannot be empty

### Default Configuration

The default personas follow a 40/20/10/30 distribution:

| Persona | Weight | Role |
|---------|--------|------|
| Rickiest Rick | 0.40 (40%) | Prime orchestrator, strategic vision, architectural rigor |
| Supportive Rick | 0.20 (20%) | Empathetic guidance, accessible explanations |
| Empathetic Rick | 0.10 (10%) | User-centric, context-aware, adaptive |
| Analytical Rick | 0.30 (30%) | Data-driven, methodical, detail-oriented |

### Example: Adding a New Persona

```json
{
  "personas": [
    {
      "name": "Rickiest Rick",
      "system_prompt": "...",
      "weight": 0.35,
      "enabled": true
    },
    {
      "name": "Supportive Rick",
      "system_prompt": "...",
      "weight": 0.20,
      "enabled": true
    },
    {
      "name": "Creative Rick",
      "system_prompt": "You are Creative Rick - innovative and experimental...",
      "weight": 0.15,
      "enabled": true
    },
    {
      "name": "Analytical Rick",
      "system_prompt": "...",
      "weight": 0.30,
      "enabled": true
    }
  ]
}
```

**Note**: Weights sum to 1.00 (0.35 + 0.20 + 0.15 + 0.30 = 1.00)

### Example: Disabling a Persona

```json
{
  "personas": [
    {
      "name": "Rickiest Rick",
      "system_prompt": "...",
      "weight": 0.50,
      "enabled": true
    },
    {
      "name": "Supportive Rick",
      "system_prompt": "...",
      "weight": 0.20,
      "enabled": false
    },
    {
      "name": "Analytical Rick",
      "system_prompt": "...",
      "weight": 0.50,
      "enabled": true
    }
  ]
}
```

**Note**: Only enabled personas count toward weight total (0.50 + 0.50 = 1.00)

### Hot-Reload

Changes to `personas.yaml` are automatically detected and reloaded without restart (Story 4.1 Task 4). The persona registry watches for file modifications and syncs changes to PostgreSQL.

### CLI Commands

Manage personas via CLI (Story 4.1 Task 3):

```bash
# List all personas with weights and status
jarvis personas list

# Add new persona interactively
jarvis personas add "Creative Rick"

# Update persona properties
jarvis personas update "Rickiest Rick" --weight 0.35

# Enable/disable personas
jarvis personas enable "Supportive Rick"
jarvis personas disable "Empathetic Rick"
```

### Database Sync

Persona configurations are persisted to PostgreSQL `agent_personas` table for:
- Audit history tracking
- Conversation metadata (which persona answered)
- Analytics and reporting

Changes via CLI or YAML hot-reload automatically sync to the database.
