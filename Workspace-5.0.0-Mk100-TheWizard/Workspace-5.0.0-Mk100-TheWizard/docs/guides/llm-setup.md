# LLM Provider Setup Guide - Unlimited Free Access

## Overview

JARVIS now supports **unlimited LLM access** through multi-provider routing:
- **OpenRouter**: 50 requests/day per free model (10+ models = 500+ requests/day)
- **Local CLIs**: Unlimited requests using your personal API keys

## Quick Start

### 1. Fix OpenRouter Privacy Setting (Required for Free Models)

Go to: **https://openrouter.ai/settings/privacy**

Enable: **"Allow free-tier usage"** (or similar option about data training)

> This lets you use free models in exchange for training data. Without this, you get 404 errors.

### 2. Add Your API Keys to `.env`

Edit `c:\Users\abast\Desktop\Workspace\.env` and add your keys:

```bash
# OpenRouter (free models - 50 req/day per model)
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

# Anthropic Claude (for claude CLI - unlimited with your key)
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE

# Google Gemini (for gemini CLI - unlimited with your key)
GOOGLE_API_KEY=YOUR_KEY_HERE

# OpenAI (for codex/gpt CLI - unlimited with your key)
OPENAI_API_KEY=sk-YOUR_KEY_HERE
```

**Note:** Leave keys blank if you don't have them. The system will skip those providers.

### 3. Rebuild Docker (One Time)

```bash
docker compose -f docker/docker-compose.yml build jarvis
```

This installs CLI tools inside the container.

### 4. Test It!

```bash
docker compose -f docker/docker-compose.yml run --rm jarvis python -c "
from jarvis.llm.client import call_llm
response = call_llm('Say hello in 5 words', provider='auto')
print(f'✅ Provider: {response.provider}')
print(f'   Response: {response.content}')
print(f'   Cost: \${response.cost_usd}')
"
```

## Provider Strategy

### Automatic Routing (Recommended)

```python
from jarvis.llm.client import call_llm

# Tries providers in order until one works:
# 1. OpenRouter (free models)
# 2. Local Claude CLI
# 3. Local Gemini CLI
# 4. Local Codex CLI
response = call_llm("Your prompt here", provider="auto")
```

### Specific Provider

```python
# Use OpenRouter only
response = call_llm("Your prompt", provider="openrouter")

# Use local Claude CLI
response = call_llm("Your prompt", provider="local-claude")

# Use local Gemini CLI
response = call_llm("Your prompt", provider="local-gemini")

# Use local Codex/OpenAI CLI
response = call_llm("Your prompt", provider="local-codex")
```

## Free OpenRouter Models (50 req/day each)

Rotate between these models for 500+ free requests/day:

1. **google/gemini-2.0-flash-exp:free** (Default, excellent quality)
2. **google/gemini-2.5-pro-exp-03-25:free** (Best quality)
3. **meta-llama/llama-4-maverick:free** (Fast)
4. **meta-llama/llama-3.3-70b-instruct:free** (Powerful)
5. **deepseek/deepseek-r1:free** (Reasoning)
6. **deepseek/deepseek-chat-v3-0324:free** (Chat)
7. **nvidia/llama-3.1-nemotron-ultra-253b-v1:free** (Large)
8. **qwen/qwq-32b:free** (Quality)
9. **google/gemma-3-27b-it:free** (Efficient)
10. **deepseek/deepseek-r1-distill-llama-70b:free** (Distilled)

Full list: https://openrouter.ai/models (filter by ":free")

## Cost Comparison

| Provider | Cost | Limit | Notes |
|----------|------|-------|-------|
| **OpenRouter free models** | $0.00 | 50/day per model | 10+ models = 500+ req/day |
| **Claude CLI** | Your API cost | Unlimited | ~$0.001-0.015 per request |
| **Gemini CLI** | Your API cost or free | Unlimited | Has generous free tier |
| **OpenAI CLI** | Your API cost | Unlimited | ~$0.002-0.06 per request |

## Usage Example - Memory Compilation

```python
# In src/jarvis/memory/compile.py

from jarvis.llm.client import call_llm

def compile_memories(conversations):
    """Compile conversation insights using LLM with automatic fallback."""

    prompt = f"""
    Analyze these conversations and extract key insights:
    {conversations}
    """

    # Auto-routing tries free providers first, falls back to paid if needed
    response = call_llm(
        prompt,
        provider="auto",  # Smart routing
        system="You are a memory compilation assistant.",
        max_tokens=2000,
    )

    print(f"Used provider: {response.provider}")
    print(f"Cost: ${response.cost_usd}")

    return response.content
```

## Troubleshooting

### OpenRouter 404 Error

**Error:** `Client error '404 Not Found'`
**Solution:** Go to https://openrouter.ai/settings/privacy and enable free-tier usage

### OpenRouter 429 Error

**Error:** `Client error '429 Too Many Requests'`
**Solution:** You hit the 50 req/day limit for that model. The system will automatically fall back to local CLIs.

### "ANTHROPIC_API_KEY not set"

**Error:** Local Claude CLI fails
**Solution:** Add `ANTHROPIC_API_KEY=sk-ant-...` to your `.env` file

### "No such file or directory: 'claude'"

**Error:** CLI wrapper not found
**Solution:** Rebuild Docker: `docker compose build jarvis`

### All Providers Failed

**Error:** `RuntimeError: All LLM providers failed`
**Solution:**
1. Check your `.env` has at least one API key set
2. Fix OpenRouter privacy setting (see above)
3. Verify keys are valid: test on provider websites

## CLI Tools Inside Container

The container includes these commands:

```bash
# Test Claude CLI
docker compose -f docker/docker-compose.yml run --rm jarvis claude "Say hello"

# Test Gemini CLI
docker compose -f docker/docker-compose.yml run --rm jarvis gemini "Say hello"

# Test Codex CLI
docker compose -f docker/docker-compose.yml run --rm jarvis codex "Say hello"
```

## Best Practices

### 1. Development (Use Free)

```python
# Use auto-routing for free access during development
response = call_llm(prompt, provider="auto")
```

### 2. Production (Use Best Quality)

```python
# Use specific provider for consistent quality
response = call_llm(prompt, provider="local-claude")  # Best quality
```

### 3. Cost Optimization

```python
# Try free first, fallback to paid only if free fails
response = call_llm(prompt, provider="auto")  # Optimal strategy
```

## Next Steps

1. ✅ Fix OpenRouter privacy setting
2. ✅ Add your API keys to `.env`
3. ✅ Rebuild Docker (`docker compose build jarvis`)
4. ✅ Test with `provider="auto"`
5. ✅ Start using in `jarvis memory compile`

## Architecture Details

**Provider Hierarchy:**
```
call_llm(provider="auto")
  ↓
ProviderRouter
  ├─ OpenRouterProvider (free models, 50 req/day each)
  ├─ LocalCLIProvider("claude") (unlimited, your API cost)
  ├─ LocalCLIProvider("gemini") (unlimited, often free tier)
  └─ LocalCLIProvider("codex") (unlimited, your API cost)
```

**Files:**
- `src/jarvis/llm/providers.py` - Provider implementations
- `src/jarvis/llm/client.py` - Main interface with routing
- `scripts/setup_cli_wrappers.sh` - CLI tool installation
- `.env` - API key configuration

---

**Questions?** The system is designed to "just work" - set your keys and use `provider="auto"`.
