import requests
import time
import json
import os

API_URL = "http://localhost:8000/api/memory"

def test_ingest():
    # 1. Create dummy file
    content = """
    Gemini 2.0 is a new multimodal AI model developed by Google DeepMind.
    It outperforms GPT-4 in many benchmarks.
    Google DeepMind is a research lab in London.
    """
    filename = "graph_test_gemini.txt"
    with open(filename, "w") as f:
        f.write(content)
        
    print(f"Post {filename} to {API_URL}/ingest...")
    
    with open(filename, "rb") as f:
        files = {"file": (filename, f, "text/plain")}
        resp = requests.post(f"{API_URL}/ingest", files=files)
        
    print(f"Status: {resp.status_code}")
    print(resp.text)
    
    if resp.status_code != 200:
        print("Ingest failed.")
        return
        
    data = resp.json()
    doc_id = data.get("doc_id")
    print(f"Doc ID: {doc_id}")
    
    # 2. Poll DB via API is hard because we don't have an endpoint for entities yet.
    # But we can query the DB directly using docker exec.
    
    print("Waiting 10s for background enrichment...")
    time.sleep(10)
    
    # Clean up
    if os.path.exists(filename):
        os.remove(filename)
        
    print("Test script finished. Check DB now.")

if __name__ == "__main__":
    test_ingest()
