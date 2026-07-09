"""Quick test to verify free LLM model works with OpenRouter."""

import sys
sys.path.insert(0, "/workspace/src")

from jarvis.llm.client import call_llm

def test_free_model():
    """Test that free model works and returns cost=$0.00"""
    print("🧪 Testing free Llama 3.1 8B model via OpenRouter...")
    print("=" * 60)

    prompt = "Write a one-sentence summary of what a RAG system does."

    try:
        response = call_llm(prompt, max_tokens=100)

        print(f"\n✅ LLM Call Successful!")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Input Tokens: {response.input_tokens}")
        print(f"   Output Tokens: {response.output_tokens}")
        print(f"   Cost: ${response.cost_usd:.4f}")
        print(f"\n📝 Response:")
        print(f"   {response.content}")

        if response.cost_usd == 0.0:
            print(f"\n🎉 CONFIRMED: Free model (cost = $0.00)")
        else:
            print(f"\n⚠️  WARNING: Cost is ${response.cost_usd}, expected $0.00 for free model")

        print("=" * 60)

    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        print(f"   Type: {type(exc).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_free_model()
