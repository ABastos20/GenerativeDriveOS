# LLM Complete Arsenal - All Guns Loaded 🔫

**Status**: November 2025
**Available Providers**: 9 (2 free, 1 cheap, 6 paid)

## Overview

JARVIS now has **complete LLM coverage** with all major AI providers integrated. The system intelligently routes through FREE/CHEAP options first, then falls back to your credits only when needed.

## Auto-Routing Priority

When you use `provider="auto"`, the system tries providers in this order:

```
1. OpenRouter (FREE) → 50 req/day per model
2. Perplexity (CHEAP) → ~$0.001 per request
3. Claude CLI → Uses your Anthropic API key
4. Gemini CLI → Uses your Google API key
5. OpenAI CLI → Uses your OpenAI API key
6. Google AI Direct API → €250 credits
7. Anthropic Direct API → Your Anthropic credits
8. OpenAI Direct API → €10 credits
```

**This gives you effectively unlimited LLM access with maximum cost protection!**

## All Available Providers

### 1. FREE TIER

#### OpenRouter (FREE)
- **Cost**: $0.00
- **Limit**: 50 requests/day per model
- **Models**: 10+ free models available
- **Quality**: Excellent (Gemini 2.0, Llama 4, DeepSeek, etc.)

```python
from jarvis.llm.client import call_llm

# Use specific free model
response = call_llm(
    "Your prompt",
    provider="openrouter",
    model="google/gemini-2.0-flash-exp:free"
)

# Or try another free model
response = call_llm(
    "Your prompt",
    provider="openrouter",
    model="meta-llama/llama-4-maverick:free"
)
```

**Available Free Models** (as of Nov 2025):
1. `google/gemini-2.0-flash-exp:free` (default, fast)
2. `google/gemini-2.5-pro-exp-03-25:free` (best quality)
3. `meta-llama/llama-4-maverick:free`
4. `meta-llama/llama-3.3-70b-instruct:free`
5. `deepseek/deepseek-r1:free` (reasoning)
6. `deepseek/deepseek-chat-v3-0324:free`
7. `nvidia/llama-3.1-nemotron-ultra-253b-v1:free`
8. `qwen/qwq-32b:free`
9. `google/gemma-3-27b-it:free`
10. `deepseek/deepseek-r1-distill-llama-70b:free`

### 2. CHEAP TIER

#### Perplexity (CHEAP)
- **Cost**: ~$0.001 per request (~€1 for 1000 requests)
- **Limit**: Unlimited
- **Quality**: Very good, fast
- **Best For**: When OpenRouter is rate-limited

```python
response = call_llm(
    "Your prompt",
    provider="perplexity"
)
```

### 3. CLI TOOLS (Use Your API Keys)

These use the official Python SDKs with your API keys. They work automatically if keys are in `.env`.

#### Claude CLI
- **Cost**: Uses your Anthropic API key
- **Model**: Claude 3.5 Sonnet
- **Best For**: Highest quality, complex reasoning

```python
response = call_llm(
    "Complex reasoning task",
    provider="local-claude"
)
```

#### Gemini CLI
- **Cost**: Uses your Google API key (€250 credits)
- **Model**: Gemini 1.5 Flash
- **Best For**: Fast, good quality

```python
response = call_llm(
    "Your prompt",
    provider="local-gemini"
)
```

#### OpenAI CLI
- **Cost**: Uses your OpenAI API key (€10 credits)
- **Model**: GPT-4o
- **Best For**: General purpose, reliable

```python
response = call_llm(
    "Your prompt",
    provider="local-codex"
)
```

### 4. DIRECT APIS (The Big Guns)

Use these explicitly when you need specific features or maximum quality.

#### Anthropic Claude API (Direct)
- **Cost**: ~$0.03 per request
- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Pricing**: $3 per 1M input tokens, $15 per 1M output tokens
- **Best For**: Complex analysis, coding, long context

```python
response = call_llm(
    "Complex multi-step problem",
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    system="You are an expert analyst"
)
```

#### Google AI Studio (Direct)
- **Cost**: ~$0.01 per request
- **Model**: Gemini 1.5 Flash (default), Gemini 1.5 Pro available
- **Pricing**: $0.075 per 1M input, $0.30 per 1M output
- **Best For**: Fast responses, multimodal, good quality

```python
response = call_llm(
    "Your prompt",
    provider="google-ai",
    model="gemini-1.5-flash",  # or "gemini-1.5-pro"
    system="You are a helpful assistant"
)
```

#### OpenAI API (Direct)
- **Cost**: ~$0.02 per request
- **Model**: GPT-4o (default), GPT-4 Turbo available
- **Pricing**: $2.50 per 1M input, $10 per 1M output
- **Best For**: Reliable, well-documented, function calling

```python
response = call_llm(
    "Your prompt",
    provider="openai",
    model="gpt-4o",  # or "gpt-4-turbo" or "gpt-3.5-turbo"
    system="You are a coding assistant"
)
```

## Usage Patterns

### Pattern 1: Always Use Auto (Recommended)

```python
from jarvis.llm.client import call_llm

# Let the system handle everything
response = call_llm("Your prompt", provider="auto")

# Cost: Usually $0.00 (OpenRouter), max ~$0.03 if all else fails
```

**This is the BEST pattern** - you get:
- Free tier first (OpenRouter)
- Cheap fallback (Perplexity ~$0.001)
- Your API keys as backup
- Direct APIs as last resort

### Pattern 2: Specific Quality Level

```python
# When you need the absolute best
response = call_llm(
    "Critical analysis requiring highest quality",
    provider="anthropic"  # Claude 3.5 Sonnet
)

# When you need good quality, fast
response = call_llm(
    "Quick question",
    provider="google-ai"  # Gemini 1.5
)
```

### Pattern 3: Cost-Conscious

```python
# Try free first, fail if unavailable
try:
    response = call_llm(prompt, provider="openrouter")
except Exception:
    # Only use paid if absolutely necessary
    response = call_llm(prompt, provider="perplexity")
```

### Pattern 4: Development vs Production

```python
import os

env = os.environ.get("JARVIS_ENV", "development")

if env == "production":
    # Production: Use reliable paid API for consistency
    provider = "anthropic"
else:
    # Development: Use free tier
    provider = "auto"

response = call_llm(prompt, provider=provider)
```

## Cost Comparison Table

| Provider | Cost/Request | Cost/1K Requests | Quality | Speed | Limit |
|----------|-------------|------------------|---------|-------|-------|
| **OpenRouter** | $0.00 | $0.00 | Excellent | Fast | 50/day per model |
| **Perplexity** | $0.001 | $1.00 | Very Good | Very Fast | Unlimited |
| **Claude CLI** | $0.03 | $30.00 | Excellent | Medium | Your credits |
| **Gemini CLI** | $0.01 | $10.00 | Very Good | Fast | €250 credits |
| **OpenAI CLI** | $0.02 | $20.00 | Good | Fast | €10 credits |
| **Anthropic API** | $0.03 | $30.00 | Excellent | Medium | Your credits |
| **Google AI API** | $0.01 | $10.00 | Very Good | Fast | €250 credits |
| **OpenAI API** | $0.02 | $20.00 | Good | Fast | €10 credits |

## Monitoring Costs

All LLM calls are logged with cost information:

```bash
# See all LLM calls
docker compose -f docker/docker-compose.yml logs jarvis | grep llm_call

# See only paid calls
docker compose -f docker/docker-compose.yml logs jarvis | grep "PAID"

# See cost summary
docker compose -f docker/docker-compose.yml logs jarvis | grep cost_usd
```

## Examples for Every Scenario

### Research & Analysis (Use Claude)
```python
response = call_llm(
    """Analyze this research paper and summarize:
    1. Main hypothesis
    2. Methodology
    3. Key findings
    4. Limitations

    Paper: [long text]""",
    provider="anthropic",  # Best for complex analysis
    max_tokens=2000
)
```

### Quick Queries (Use Auto)
```python
response = call_llm(
    "What is the capital of France?",
    provider="auto",  # Will use free tier
    max_tokens=50
)
```

### Code Generation (Use Claude or GPT-4o)
```python
response = call_llm(
    """Write a Python function that:
    - Takes a list of dictionaries
    - Filters by a key-value pair
    - Returns sorted results

    Include docstring and type hints.""",
    provider="anthropic",  # or "openai" for GPT-4o
    system="You are an expert Python developer"
)
```

### Batch Processing (Use Perplexity or Free Tier)
```python
# Process 1000 items
for item in items:
    response = call_llm(
        f"Summarize: {item}",
        provider="auto",  # Tries free, falls back to cheap
        max_tokens=100
    )
    # Cost: ~$0-1 total for 1000 items
```

## Configuration

All API keys are in [.env](.env):

```bash
# FREE (always use first)
OPENROUTER_API_KEY=sk-or-v1-...

# CHEAP (fallback)
PERPLEXITY_API_KEY=pplx-...

# YOUR CREDITS (use when needed)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-proj-...
```

## Safety Features

✅ **Cost Protection**: Auto-routing tries free/cheap first
✅ **Warning Logs**: All paid API calls log ⚠️ warnings
✅ **Cost Tracking**: Every call logged with exact cost
✅ **Fallback Chain**: 8 providers ensure you always get a response
✅ **No Surprises**: Must explicitly use expensive providers

## When to Use What

| Use Case | Best Provider | Why |
|----------|---------------|-----|
| **Development/Testing** | `auto` | Free, safe, reliable |
| **Production (Quality)** | `anthropic` | Most capable, consistent |
| **Production (Speed)** | `google-ai` | Fast, good quality |
| **Production (Cost)** | `auto` | Cheapest, smart fallback |
| **Complex Reasoning** | `anthropic` | Claude excels at this |
| **Code Generation** | `anthropic` or `openai` | Both excellent |
| **Quick Queries** | `auto` | Fast, free |
| **Batch Processing** | `auto` or `perplexity` | Cost-effective |
| **Long Context** | `anthropic` | Best context handling |
| **Multimodal** | `google-ai` | Supports vision, audio |

## Summary

You now have **9 LLM providers** at your disposal:
- 🆓 **2 FREE** (OpenRouter models)
- 💰 **1 CHEAP** (Perplexity ~$0.001)
- 🔧 **3 CLI Tools** (your API keys)
- 🚀 **3 Direct APIs** (premium quality)

**Default behavior (`provider="auto"`)**: Tries FREE → CHEAP → Your Keys → Direct APIs

**Your Credits Protected**: Must explicitly call expensive providers

**Bottom Line**: Use `provider="auto"` for everything. The system will handle the rest intelligently!

---

**Documentation**: [docs/LLM_COST_PROTECTION.md](LLM_COST_PROTECTION.md)
**Last Updated**: November 2025
