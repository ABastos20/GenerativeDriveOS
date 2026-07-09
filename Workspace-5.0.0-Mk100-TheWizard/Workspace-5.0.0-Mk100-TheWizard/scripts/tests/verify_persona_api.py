import asyncio
import httpx
import sys

API_URL = "http://localhost:8000"
USER_ID = "00000000-0000-0000-0000-000000000001" # Genesis Admin

async def ask_with_persona(persona: str):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"\n--- Testing Persona: {persona} ---")
            response = await client.post(
                f"{API_URL}/api/chat",
                headers={"X-User-ID": USER_ID},
                json={
                    "message": "Who are you and what is your style?",
                    "agent_persona": persona,
                    "stream": False # Simple check
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data.get('response')[:200]}...")
                return data.get('response')
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

async def main():
    print("🚀 Verifying Persona Backend Logic...")
    
    # Test Copilot
    r1 = await ask_with_persona("copilot")
    
    # Test Iron Man
    r2 = await ask_with_persona("iron_man")
    
    # Test Advisor
    r3 = await ask_with_persona("advisor")
    
    if r1 and r2 and r3:
        print("\n✅ All Personas Responded.")
        if r1 != r2 and r2 != r3:
            print("✅ Responses are DIFFERENT (Persona Logic Active).")
        else:
            print("❌ Responses are IDENTIAL (Persona Logic Failed).")
    else:
        print("❌ Verification Incomplete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
