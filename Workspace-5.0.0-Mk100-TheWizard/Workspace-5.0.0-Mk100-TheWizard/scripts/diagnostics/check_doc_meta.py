
import sys
import os
sys.path.append(os.getcwd() + "/src")

from jarvis.database.postgres import get_session
from jarvis.database.models import Document

def check_one_doc_metadata():
    target = "file::/workspace/docs/sprints/epic-3-prep-checklist.md"
    with get_session() as session:
        doc = session.query(Document).filter(Document.doc_key == target).one_or_none()
        if doc:
            print(f"Key: {doc.doc_key}")
            print(f"Domain: {doc.domain}")
            print(f"Metadata: {doc.metadata_}")
        else:
            print("Doc not found")


if __name__ == "__main__":
    check_one_doc_metadata()

    target2 = "file::/workspace/docs/jarvis/operating-manual.md"
    with get_session() as session:
        doc = session.query(Document).filter(Document.doc_key == target2).one_or_none()
        if doc:
            print(f"Key: {doc.doc_key}")
            print(f"Domain: {doc.domain}")
            print(f"Metadata: {doc.metadata_}")
        else:
            print(f"{target2} not found")

