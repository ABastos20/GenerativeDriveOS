import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

print("Testing imports...")

try:
    print("Importing jarvis.api.chat...")
    from jarvis.api import chat
    print("✅ jarvis.api.chat imported successfully")
except Exception as e:
    print(f"❌ Failed to import jarvis.api.chat: {e}")
    sys.exit(1)

try:
    print("Importing jarvis.memory.search...")
    from jarvis.memory import search
    print("✅ jarvis.memory.search imported successfully")
except Exception as e:
    print(f"❌ Failed to import jarvis.memory.search: {e}")
    sys.exit(1)

print("All imports passed!")
