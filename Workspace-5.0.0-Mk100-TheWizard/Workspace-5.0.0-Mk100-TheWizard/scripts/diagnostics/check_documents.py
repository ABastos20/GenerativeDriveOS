
import sys
import os
sys.path.append(os.getcwd() + "/src")

from jarvis.database.postgres import get_session
from jarvis.database.models import Document

def check_docs():
    with get_session() as session:
        count = session.query(Document).count()
        print(f"Total documents: {count}")
        
        if count > 0:
            print("First 5 keys:")
            docs = session.query(Document).limit(5).all()
            for d in docs:
                print(f" - {d.doc_key}")
        else:
            print("Documents table is empty!")

if __name__ == "__main__":
    check_docs()
