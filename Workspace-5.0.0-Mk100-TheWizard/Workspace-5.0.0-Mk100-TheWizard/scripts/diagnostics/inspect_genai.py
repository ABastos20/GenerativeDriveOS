
import google.generativeai as genai

print(f"Version: {genai.__version__}")

tool_fields = dir(genai.protos.Tool)
if "google_search" in tool_fields:
    print("FOUND: google_search in Tool fields")
else:
    print("NOT FOUND: google_search in Tool fields")

if "google_search_retrieval" in tool_fields:
    print("FOUND: google_search_retrieval in Tool fields")

print("\nProtos starting with GoogleSearch:")
for name in dir(genai.protos):
    if name.startswith("GoogleSearch"):
        print(name)
