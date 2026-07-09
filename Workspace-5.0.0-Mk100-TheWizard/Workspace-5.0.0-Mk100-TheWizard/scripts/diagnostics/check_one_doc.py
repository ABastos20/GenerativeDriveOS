
import sys
import os
sys.path.append(os.getcwd() + "/src")

from jarvis.database.postgres import get_session
from jarvis.database.models import Document

def check_one_doc():
    target = "file::/workspace/docs/sprints/epic-3-prep-checklist.md"
    with get_session() as session:
        doc = session.query(Document).filter(Document.doc_key == target).one_or_none()
        if doc:
            print(f"FOUND: {doc.doc_key}")
        else:
            print(f"NOT FOUND: {target}")
            # List close matches?
            print("Listing all keys starting with file::/workspace/docs/sprints/")
            docs = session.query(Document).filter(Document.doc_key.like("file::/workspace/docs/sprints/%")).all()
            for d in docs:
                print(f" - {d.doc_key}")

if __name__ == "__main__":
    check_one_doc()
