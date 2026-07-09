import asyncio
import httpx
import os
import sys

# Configuration
API_URL = "http://localhost:8000"
KEYCLOAK_URL = "http://localhost:8081"
REALM = "jarvis"
CLIENT_ID = "jarvis-ui"
USERNAME = "admin"
PASSWORD = "password"
LEGACY_USER_ID = "0c193d00-8849-434c-b7d2-af6478e94c59"  # Admin user

async def test_legacy_auth():
    print(f"\n[Test] Legacy Auth (X-User-ID)")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/api/governance/dashboard/system",
                headers={"X-User-ID": LEGACY_USER_ID}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Legacy Auth Success")
                users = response.json()
                print(f"Response: {str(users)[:100]}...")
            else:
                print(f"❌ Legacy Auth Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_oidc_auth():
    print(f"\n[Test] OIDC Auth (Keycloak Bearer Token)")
    
    # 1. Get Token
    token = None
    async with httpx.AsyncClient() as client:
        try:
            data = {
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "username": USERNAME,
                "password": PASSWORD
            }
            token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
            print(f"Fetching token from {token_url}...")
            resp = await client.post(token_url, data=data)
            
            if resp.status_code != 200:
                print(f"❌ Failed to get token: {resp.text}")
                return

            token = resp.json().get("access_token")
            print("✅ Token acquired")
        except Exception as e:
            print(f"❌ Keycloak Connection Error: {e}")
            return

    # 2. Use Token
    if token:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{API_URL}/api/governance/proposals",
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ OIDC Auth Success")
                    # Check if user was auto-provisioned?
                    # We can check headers or logs, but 200 implies middleware passed.
                else:
                    print(f"❌ OIDC Auth Failed: {response.text}")
            except Exception as e:
                print(f"❌ Error: {e}")

async def test_invalid_auth():
    print(f"\n[Test] Invalid Auth (Bad Token)")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/api/governance/proposals",
                headers={"Authorization": "Bearer invalid_token_123"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 401:
                print("✅ Invalid Token Rejected (401)")
            else:
                print(f"❌ Unexpected Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    print("🚀 Starting Auth Compatibility Verification...")
    await test_legacy_auth()
    await test_oidc_auth()
    await test_invalid_auth()

if __name__ == "__main__":
    asyncio.run(main())
