"""Quick OpenRouter test with updated headers."""
import sys
sys.path.insert(0, "/workspace/src")

from jarvis.llm.providers import OpenRouterProvider

print("Testing OpenRouter with proper headers...")
provider = OpenRouterProvider()
print(f"API key configured: {provider.is_available()}")

try:
    # Test raw API call with debug
    import httpx
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/anthropics/jarvis",
        "X-Title": "JARVIS",
    }
    payload = {
        "model": provider.model,
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 20,
    }

    print(f"Calling: {provider.base_url}/chat/completions")
    print(f"Model: {provider.model}")
    print(f"API Key: {provider.api_key[:20]}...")

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{provider.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        print(f"\nHTTP Status: {resp.status_code}")
        print(f"Response Body: {resp.text[:500]}")
        resp.raise_for_status()

    print("\n✅ Success!")
    data = resp.json()
    print(f"Response: {data}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
