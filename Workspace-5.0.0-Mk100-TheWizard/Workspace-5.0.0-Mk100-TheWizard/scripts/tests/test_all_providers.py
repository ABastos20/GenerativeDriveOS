#!/usr/bin/env python3
"""Test all LLM providers to verify configuration."""
import sys
sys.path.insert(0, "/workspace/src")

from jarvis.llm.client import call_llm
import structlog

logger = structlog.get_logger(__name__)

print("=" * 70)
print("  JARVIS Multi-Provider LLM Test - All Providers")
print("=" * 70)
print()

# Test each provider with minimal prompts to avoid wasting credits
providers = [
    ("auto", "Auto-routing (tries all in order)"),
    ("openrouter", "OpenRouter (free Gemini)"),
    ("perplexity", "Perplexity (Sonar)"),
    ("local-claude", "Claude CLI"),
    ("local-gemini", "Gemini CLI"),
    ("local-codex", "OpenAI CLI"),
]

results = []

for provider_name, description in providers:
    print(f"\n{'='*70}")
    print(f"Testing: {description}")
    print(f"Provider: {provider_name}")
    print("-" * 70)

    try:
        # Use minimal prompt to minimize cost
        response = call_llm("Hi", provider=provider_name, max_tokens=10)

        status = "✅ WORKING"
        print(f"{status}")
        print(f"   Model: {response.model}")
        print(f"   Response: {response.content[:50]}...")
        print(f"   Tokens: {response.input_tokens} in / {response.output_tokens} out")
        print(f"   Cost: ${response.cost_usd:.6f}")

        results.append((provider_name, description, "✅", None))

    except Exception as exc:
        status = "❌ FAILED"
        error_msg = str(exc)[:100]
        print(f"{status}")
        print(f"   Error: {error_msg}...")

        results.append((provider_name, description, "❌", error_msg))

# Summary
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
print()

working_count = sum(1 for r in results if r[2] == "✅")
total_count = len(results)

for provider_name, description, status, error in results:
    print(f"{status} {provider_name:15} - {description}")
    if error:
        if "ANTHROPIC_API_KEY" in error:
            print(f"     → CLI not configured (needs login)")
        elif "GOOGLE_API_KEY" in error or "GOOGLE_GENAI_API_KEY" in error:
            print(f"     → CLI not configured (needs login)")
        elif "OPENAI_API_KEY" in error:
            print(f"     → CLI not configured (needs login)")

print()
print(f"Working providers: {working_count}/{total_count}")
print()

if working_count > 0:
    print("✅ LLM integration is operational!")
    print("   You can now use provider='auto' for automatic fallback.")
else:
    print("⚠️  No providers are working. Check API keys in .env")

print()
print("=" * 70)
print("  NOTES")
print("=" * 70)
print()
print("Local CLIs require login:")
print("  1. Start container: docker compose -f docker/docker-compose.yml run --rm jarvis bash")
print("  2. Inside container, run CLI login commands:")
print("     - Claude: Follow prompts if needed")
print("     - Gemini: May need gcloud auth")
print("     - OpenAI: Check API key setup")
print()
print("API-based providers (OpenRouter, Perplexity) work directly from .env keys.")
