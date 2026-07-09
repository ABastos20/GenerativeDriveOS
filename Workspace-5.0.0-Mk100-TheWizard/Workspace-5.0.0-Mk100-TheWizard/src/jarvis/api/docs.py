"""Document retrieval API for full document viewer (Story 4-9).

Provides endpoint to fetch full document content by doc_key,
enabling the 'View full document' feature in the chat UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.jarvis.database.models import Document
from src.jarvis.database.postgres import get_session_factory

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["docs"])

# Maximum content size to return inline (100KB)
MAX_INLINE_CONTENT_BYTES = 100 * 1024


def get_db():
    """FastAPI dependency to get a database session."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {exc}",
        ) from exc
    finally:
        session.close()


def _resolve_document(session: Session, doc_key: str) -> Optional[Document]:
    """Resolve document by doc_key with fallback to filename match.
    
    Priority:
    1. Exact match on doc_key
    2. Filename match on source_file
    
    Returns:
        Document if found, None otherwise
    """
    # Try exact match
    doc = session.execute(
        select(Document).where(Document.doc_key == doc_key)
    ).scalar_one_or_none()
    
    # Fallback: Try filename match
    if not doc:
        doc = session.execute(
            select(Document).where(Document.source_file.endswith(doc_key))
        ).scalars().first()
    
    return doc


def _read_document_content(doc: Document) -> tuple[Optional[str], int]:
    """Read document content from DB or filesystem.
    
    Returns:
        (content,  full_size_bytes) tuple
    """
    content: Optional[str] = None
    
    # Prefer DB content
    if hasattr(doc, "content") and doc.content:
        content = doc.content
    # Fallback: Read from filesystem
    elif hasattr(doc, "source_file") and doc.source_file:
        try:
            file_path = Path(doc.source_file)
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(
                "document_file_read_failed",
                doc_key=doc.doc_key,
                path=doc.source_file,
                error=str(e),
            )
    
    full_size = len(content.encode("utf-8")) if content else 0
    return content, full_size


def _render_html_view(doc: Document, content: str, full_size: int) -> str:
    """Render document as styled HTML page.
    
    Returns:
        HTML string for full-page viewing
    """
    filename = Path(doc.source_file).name if doc.source_file else doc.doc_key
    domain = getattr(doc, "domain", "")
    safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{filename} - JARVIS Document Viewer</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #050816;
      color: #e5e7eb;
      padding: 24px 48px;
      line-height: 1.6;
      max-width: 900px;
      margin: 0 auto;
    }}
    h1 {{
      color: #38bdf8;
      font-size: 24px;
      margin-bottom: 8px;
      border-bottom: 1px solid rgba(56, 189, 248, 0.3);
      padding-bottom: 12px;
    }}
    .meta {{
      color: #94a3b8;
      font-size: 13px;
      margin-bottom: 24px;
    }}
    pre {{
      background: #0f172a;
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 13px;
    }}
    .back-link {{
      display: inline-block;
      margin-bottom: 16px;
      color: #38bdf8;
      text-decoration: none;
    }}
    .back-link:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <a href="/chat" class="back-link">&larr; Back to Chat</a>
  <h1>{filename}</h1>
  <div class="meta">Domain: {domain} &bull; Size: {full_size // 1024} KB</div>
  <pre>{safe_content}</pre>
</body>
</html>'''


@router.get(
    "/docs/{doc_key:path}",
    summary="Get full document content",
    description=(
        "Fetch full document content by doc_key for the 'View full document' feature. "
        "Content is capped at 100KB for inline display; larger docs return truncated content. "
        "Use format=html for styled full-page viewing in a new tab."
    ),
)
def get_document(
    doc_key: str,
    format: Optional[str] = None,
    session: Session = Depends(get_db),
):
    """Retrieve full document content by doc_key.
    
    Priority:
    1. Postgres Document table (source of truth)
    2. Filesystem fallback via stored path
    
    Args:
        format: Optional format - 'html' returns styled HTML page for new tab viewing
    """
    logger.info("get_document_request", doc_key=doc_key, format=format)
    
    # Resolve document
    doc = _resolve_document(session, doc_key)
    if not doc:
        logger.warning("document_not_found", doc_key=doc_key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_key}' not found",
        )
    
    # Read content
    content, full_content_bytes = _read_document_content(doc)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_key}' content not available",
        )
    
    is_large = full_content_bytes > MAX_INLINE_CONTENT_BYTES
    
    # HTML format: Return styled full-page view
    if format == "html":
        html = _render_html_view(doc, content, full_content_bytes)
        logger.info("document_html_served", doc_key=doc_key, size=full_content_bytes)
        return HTMLResponse(content=html)
    
    # Apply size limit for inline JSON display
    if is_large:
        content = content[:MAX_INLINE_CONTENT_BYTES // 4]  # Rough char estimate
        content += "\n\n... (Content truncated. Document too large for inline display.)"
        truncated = True
    
    logger.info(
        "document_retrieved",
        doc_key=doc_key,
        content_length=len(content),
        full_size=full_content_bytes,
        is_large=is_large,
        truncated=truncated,
    )
    
    return {
        "doc_key": doc.doc_key,
        "domain": getattr(doc, "domain", None),
        "path": getattr(doc, "path", None),
        "content": content,
        "truncated": truncated,
        "content_size": full_content_bytes,
        "is_large": is_large,
    }
