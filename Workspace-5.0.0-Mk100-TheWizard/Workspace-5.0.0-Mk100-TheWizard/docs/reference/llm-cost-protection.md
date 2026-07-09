# LLM Cost Protection - November 2025

## 🛡️ CREDIT PROTECTION ENABLED

Your LLM integration is configured to **PROTECT YOUR CREDITS** by default.

### Your Credits:
- **Google/Gemini**: €250 credits ⚠️ EXPENSIVE
- **OpenAI**: €10 credits ⚠️ EXPENSIVE
- **Anthropic/Claude**: API key configured ⚠️ EXPENSIVE

### Auto-Routing Strategy (SAFE):

When you use `provider="auto"`, the system will **ONLY** try:

1. **OpenRouter** - FREE (50 requests/day per model, 10+ models available)
2. **Perplexity** - CHEAP (~$0.001 per request, only if OpenRouter fails)

**The system will NOT automatically use your expensive credits!**

## Usage Guidelines

### ✅ Safe (Use Freely):

```python
from jarvis.llm.client import call_llm

# This is SAFE - uses free tier first, cheap fallback
response = call_llm("Your prompt", provider="auto")

# Also safe - explicitly using free tier
response = call_llm("Your prompt", provider="openrouter")
```

**Cost**: $0.00 - $0.001 per request

### ⚠️ Paid (Use Sparingly):

```python
# This costs ~$0.001 per request
response = call_llm("Your prompt", provider="perplexity")
```

**Cost**: ~$0.001 per request

### 🚨 EXPENSIVE (Only When Necessary):

```python
# These use your valuable credits - only use explicitly!
response = call_llm("Your prompt", provider="local-claude")   # €250 Google credits
response = call_llm("Your prompt", provider="local-gemini")   # €250 Google credits
response = call_llm("Your prompt", provider="local-codex")    # €10 OpenAI credits
```

**Cost**: $0.01 - $0.10 per request (100x more expensive!)

## Cost Comparison

| Provider | Cost per Request | When to Use |
|----------|------------------|-------------|
| **OpenRouter** | FREE ($0.00) | Default - use always |
| **Perplexity** | ~$0.001 | Fallback when OpenRouter rate limited |
| **Claude CLI** | ~$0.03 | ONLY for critical tasks requiring best quality |
| **Gemini CLI** | ~$0.01 | AVOID - uses your €250 credits |
| **OpenAI CLI** | ~$0.02 | AVOID - uses your €10 credits |

## Free Tier Capacity

**OpenRouter provides 10+ free models**, each with 50 requests/day:

1. `google/gemini-2.0-flash-exp:free` (default)
2. `google/gemini-2.5-pro-exp-03-25:free`
3. `meta-llama/llama-4-maverick:free`
4. `meta-llama/llama-3.3-70b-instruct:free`
5. `deepseek/deepseek-r1:free`
6. ... and 5+ more

**Total free capacity**: 500+ requests/day across all models

## Monitoring Costs

Check your LLM costs in logs:

```bash
# See all LLM calls with costs
docker compose -f docker/docker-compose.yml logs jarvis | grep llm_call_completed

# See only paid calls
docker compose -f docker/docker-compose.yml logs jarvis | grep "cost_usd" | grep -v "0.0"
```

## Best Practices

### Development (FREE):
```python
# Always use auto for development
response = call_llm(prompt, provider="auto", max_tokens=500)
```

### Production (COST-AWARE):
```python
# Still use auto - it's protected
response = call_llm(prompt, provider="auto")

# Only if you REALLY need Claude quality:
if critical_task:
    response = call_llm(prompt, provider="local-claude")
```

### Token Limits (SAVE MONEY):
```python
# Be conservative with max_tokens
response = call_llm(
    prompt,
    provider="auto",
    max_tokens=500  # Not 4000! Lower = cheaper
)
```

## Emergency: Disable Perplexity

If you want ONLY free tier (no Perplexity fallback at all):

Edit [src/jarvis/llm/client.py](../src/jarvis/llm/client.py):

```python
# Remove Perplexity from auto-routing
router = ProviderRouter(
    providers=[
        OpenRouterProvider(model=model),  # FREE only
        # PerplexityProvider(),  # REMOVED - no fallback
    ]
)
```

Then the system will only use OpenRouter (100% free) and fail if rate limited.

## Cost Alerts

The system logs:
- ✅ `llm_call_completed` with `cost_usd=0.0` - FREE
- ⚠️ `llm_call_completed` with `cost_usd>0` - PAID

Watch for paid calls in your logs!

## Summary

🛡️ **Protection Enabled**: `provider="auto"` will NOT use expensive APIs
✅ **Free Tier**: 500+ requests/day via OpenRouter
💰 **Cheap Fallback**: Perplexity at ~$0.001 per request
🚨 **Expensive APIs**: Must be called explicitly

**Bottom line**: Use `provider="auto"` freely - your credits are protected!

---

**Last Updated**: November 2025
**Your Credits**: €250 (Google) + €10 (OpenAI) - Protected by default
