import asyncio
import httpx
import sys

KEYCLOAK_URL = "http://keycloak:8080"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"
REALM = "jarvis"

USERS = {
    "user1": "cf87954a-70b6-498e-b770-a3cacb254ae3",
    "observer1": "36fe9c3a-d3ef-4eb6-8d44-ccd828e2cf02"
}

async def get_admin_token():
    print("🔑 Getting Admin Token...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": ADMIN_USER,
                "password": ADMIN_PASS
            }
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        else:
            print(f"❌ Failed to get admin token: {resp.text}")
            sys.exit(1)

async def fix_user(token, username, user_id):
    print(f"🔧 Fixing user {username} ({user_id})...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        # 1. Update User Profile (Enabled, Email Verified, Names)
        data = {
            "enabled": True,
            "emailVerified": True,
            "firstName": username.capitalize(),
            "lastName": "Test",
            "requiredActions": [] 
        }
        resp = await client.put(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}",
            headers=headers,
            json=data
        )
        if resp.status_code == 204:
            print(f"  ✅ Profile Updated")
            # Verify state
            get_resp = await client.get(f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}", headers=headers)
            print(f"  Current State: {get_resp.json()}")
        else:
            print(f"  ❌ Profile Update Failed: {resp.text}")

        # 2. Reset Password
        pwd_data = {
            "type": "password",
            "value": "password",
            "temporary": False
        }
        resp = await client.put(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/reset-password",
            headers=headers,
            json=pwd_data
        )
        if resp.status_code == 204:
            print(f"  ✅ Password Reset")
        else:
            print(f"  ❌ Password Reset Failed: {resp.text}")

async def main():
    token = await get_admin_token()
    for username, uid in USERS.items():
        await fix_user(token, username, uid)
    print("✅ All repairs complete.")

if __name__ == "__main__":
    asyncio.run(main())
