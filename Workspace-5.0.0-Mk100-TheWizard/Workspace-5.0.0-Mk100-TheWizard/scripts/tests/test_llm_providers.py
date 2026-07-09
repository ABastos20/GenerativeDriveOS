"""Test multi-provider LLM integration with automatic fallback."""

import sys
sys.path.insert(0, "/workspace/src")

from jarvis.llm.client import call_llm


def test_auto_provider():
    """Test automatic provider fallback."""
    print("🧪 Testing Auto Provider Routing")
    print("=" * 60)
    print("Strategy: OpenRouter → Claude CLI → Gemini CLI → Codex CLI")
    print("=" * 60)

    prompt = "Write a one-sentence summary of what a RAG system does."

    try:
        print("\n🔄 Calling with provider='auto' (automatic fallback)...")
        response = call_llm(prompt, provider="auto", max_tokens=100)

        print(f"\n✅ LLM Call Successful!")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Input Tokens: {response.input_tokens}")
        print(f"   Output Tokens: {response.output_tokens}")
        print(f"   Cost: ${response.cost_usd:.4f}")
        print(f"\n📝 Response:")
        print(f"   {response.content[:200]}...")

        if response.cost_usd == 0.0:
            print(f"\n🎉 CONFIRMED: Free provider (cost = $0.00)")

        if response.provider.startswith("local-"):
            print(f"   Note: Used local CLI tool (unlimited, free)")

        print("=" * 60)

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        print(f"   Type: {type(exc).__name__}")
        import traceback
        traceback.print_exc()


def test_specific_providers():
    """Test specific provider selections."""
    print("\n\n🧪 Testing Specific Providers")
    print("=" * 60)

    prompt = "Say 'hello' in one word."

    providers = [
        ("openrouter", "OpenRouter API (free Gemini)"),
        ("local-claude", "Local Claude CLI"),
        ("local-gemini", "Local Gemini CLI"),
        ("local-codex", "Local Codex CLI"),
    ]

    for provider_name, description in providers:
        print(f"\n🔧 Testing: {description}")
        print(f"   Provider: {provider_name}")

        try:
            response = call_llm(prompt, provider=provider_name, max_tokens=20)
            print(f"   ✅ Success!")
            print(f"   Response: {response.content[:50]}")
            print(f"   Cost: ${response.cost_usd:.4f}")
        except Exception as exc:
            print(f"   ⚠️  Failed: {type(exc).__name__}: {str(exc)[:80]}")

    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  JARVIS Multi-Provider LLM Test Suite")
    print("="*60 + "\n")

    test_auto_provider()
    test_specific_providers()

    print("\n\n✅ Test Suite Complete!")
    print("\nℹ️  Recommendation: Use provider='auto' for unlimited free access")
    print("   with automatic fallback when rate limits hit.")
