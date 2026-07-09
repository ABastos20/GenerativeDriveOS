#!/usr/bin/env python3
"""Bootstrap JARVIS memory system with core docs and GPT conversations.

This master script:
1. Initializes Qdrant collection (if needed)
2. Ingests Jarvis core docs (persona, operating-manual)
3. Ingests GPT export conversations
4. Validates with health check

Usage (inside Docker container):
    python scripts/bootstrap_jarvis_memory.py
    python scripts/bootstrap_jarvis_memory.py --skip-gpt  # Skip GPT conversations
    python scripts/bootstrap_jarvis_memory.py --dry-run   # Show what would be done
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog
from qdrant_client.http import models as qmodels

from jarvis.database.qdrant import (
    get_qdrant_client,
    collection_exists,
    init_collection,
    get_collection_info,
)
from jarvis.memory.ingest import ingest_file

logger = structlog.get_logger(__name__)


def bootstrap_collection(dry_run: bool = False) -> bool:
    """Ensure Qdrant collection is initialized."""
    logger.info("step_1_initialize_collection")

    if dry_run:
        logger.info("dry_run_would_initialize_collection")
        return True

    try:
        client = get_qdrant_client()

        if collection_exists("knowledge", client=client):
            info = get_collection_info("knowledge", client=client)
            logger.info(
                "collection_exists",
                points_count=info.points_count,
                vector_size=info.config.params.vectors.size,
            )
            return True

        init_collection(collection_name="knowledge", client=client)
        logger.info("collection_initialized")
        return True

    except Exception as e:
        logger.error("collection_init_failed", error=str(e))
        return False


def ingest_jarvis_docs(dry_run: bool = False) -> int:
    """Ingest Jarvis core documentation."""
    logger.info("step_2_ingest_jarvis_docs")

    docs_dir = Path("docs/jarvis")
    core_docs = [
        ("persona.md", "jarvis-core"),
        ("operating-manual.md", "jarvis-core"),
    ]

    total_chunks = 0

    for doc_name, domain in core_docs:
        doc_path = docs_dir / doc_name

        if not doc_path.exists():
            logger.warning("doc_not_found", path=str(doc_path))
            continue

        if dry_run:
            logger.info("dry_run_would_ingest", path=str(doc_path), domain=domain)
            continue

        try:
            result = ingest_file(doc_path, domain=domain)
            total_chunks += result.chunks
            logger.info(
                "doc_ingested",
                path=str(doc_path),
                chunks=result.chunks,
                points=result.points_written,
            )
        except Exception as e:
            logger.error("doc_ingest_failed", path=str(doc_path), error=str(e))

    logger.info("jarvis_docs_complete", total_chunks=total_chunks)
    return total_chunks


def load_gpt_conversations(export_path: Path) -> List[Dict[str, Any]]:
    """Load conversations from GPT export JSON."""
    with open(export_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def extract_conversation_messages(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract messages from conversation structure."""
    messages = []
    mapping = conversation.get('mapping', {})

    for node_id, node_data in mapping.items():
        message_data = node_data.get('message')
        if not message_data:
            continue

        content = message_data.get('content', {})
        if not content or content.get('content_type') != 'text':
            continue

        parts = content.get('parts', [])
        if not parts or not parts[0]:
            continue

        text = parts[0] if isinstance(parts[0], str) else str(parts[0])

        messages.append({
            'id': node_id,
            'role': message_data.get('author', {}).get('role', 'unknown'),
            'text': text,
            'create_time': message_data.get('create_time'),
        })

    return messages


def chunk_conversation(conversation: Dict[str, Any], max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
    """Chunk conversation into smaller pieces."""
    messages = extract_conversation_messages(conversation)

    title = conversation.get('title', 'Untitled')
    create_time = conversation.get('create_time', time.time())
    conv_id = conversation.get('id', str(uuid4()))

    chunks = []
    current_chunk = []
    current_size = 0

    for msg in messages:
        msg_text = f"{msg['role']}: {msg['text']}\n\n"
        msg_size = len(msg_text)

        if current_size + msg_size > max_chunk_size and current_chunk:
            chunk_text = "".join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'title': title,
                'conversation_id': conv_id,
                'create_time': create_time,
                'chunk_index': len(chunks),
            })
            current_chunk = []
            current_size = 0

        current_chunk.append(msg_text)
        current_size += msg_size

    if current_chunk:
        chunk_text = "".join(current_chunk)
        chunks.append({
            'text': chunk_text,
            'title': title,
            'conversation_id': conv_id,
            'create_time': create_time,
            'chunk_index': len(chunks),
        })

    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using sentence-transformers."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]


def ingest_gpt_conversations(export_path: Path, dry_run: bool = False) -> int:
    """Ingest GPT export conversations."""
    logger.info("step_3_ingest_gpt_conversations", path=str(export_path))

    if not export_path.exists():
        logger.error("gpt_export_not_found", path=str(export_path))
        return 0

    conversations = load_gpt_conversations(export_path)
    logger.info("gpt_conversations_loaded", count=len(conversations))

    if dry_run:
        total_chunks = 0
        for conv in conversations:
            chunks = chunk_conversation(conv)
            total_chunks += len(chunks)
            logger.info(
                "dry_run_conversation",
                title=conv.get('title'),
                chunks=len(chunks),
            )
        logger.info("dry_run_gpt_total", total_chunks=total_chunks)
        return total_chunks

    client = get_qdrant_client()
    total_points = 0

    for i, conv in enumerate(conversations):
        title = conv.get('title', 'Untitled')
        logger.info("processing_conversation", index=i+1, total=len(conversations), title=title)

        chunks = chunk_conversation(conv)
        if not chunks:
            continue

        try:
            # Generate embeddings for all chunks
            texts = [chunk['text'] for chunk in chunks]
            embeddings = generate_embeddings(texts)

            # Create points
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point = qmodels.PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload={
                        'text': chunk['text'],
                        'title': chunk['title'],
                        'conversation_id': chunk['conversation_id'],
                        'chunk_index': chunk['chunk_index'],
                        'source': 'gpt_export',
                        'domain': 'jarvis-conversations',
                        'create_time': chunk['create_time'],
                        'ingested_at': datetime.now(timezone.utc).isoformat(),
                    }
                )
                points.append(point)

            # Upsert to Qdrant
            client.upsert(collection_name="knowledge", points=points)
            total_points += len(points)
            logger.info("conversation_ingested", title=title, chunks=len(points))

        except Exception as e:
            logger.error("conversation_ingest_failed", title=title, error=str(e))

    logger.info("gpt_conversations_complete", total_points=total_points)
    return total_points


def validate_ingestion() -> bool:
    """Validate ingestion with health check."""
    logger.info("step_4_validate")

    try:
        client = get_qdrant_client()
        info = get_collection_info("knowledge", client=client)

        logger.info(
            "validation_success",
            points_count=info.points_count,
            vector_size=info.config.params.vectors.size,
            distance=info.config.params.vectors.distance.value,
        )

        return info.points_count > 0

    except Exception as e:
        logger.error("validation_failed", error=str(e))
        return False


def main() -> int:
    """Main bootstrap workflow."""
    parser = argparse.ArgumentParser(
        description="Bootstrap JARVIS memory with core docs and GPT conversations"
    )
    parser.add_argument(
        "--skip-gpt",
        action="store_true",
        help="Skip GPT conversation ingestion"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be done"
    )
    parser.add_argument(
        "--gpt-export",
        type=Path,
        default=Path("docs/gpt export/conversations.json"),
        help="Path to GPT export conversations.json"
    )

    args = parser.parse_args()

    logger.info(
        "bootstrap_started",
        dry_run=args.dry_run,
        skip_gpt=args.skip_gpt,
    )

    # Step 1: Initialize collection
    if not bootstrap_collection(dry_run=args.dry_run):
        logger.error("bootstrap_failed_at_collection_init")
        return 1

    # Step 2: Ingest Jarvis docs
    jarvis_chunks = ingest_jarvis_docs(dry_run=args.dry_run)

    # Step 3: Ingest GPT conversations
    gpt_points = 0
    if not args.skip_gpt:
        gpt_points = ingest_gpt_conversations(args.gpt_export, dry_run=args.dry_run)
    else:
        logger.info("skipping_gpt_conversations")

    # Step 4: Validate
    if not args.dry_run:
        if not validate_ingestion():
            logger.warning("validation_incomplete")

    logger.info(
        "bootstrap_complete",
        jarvis_chunks=jarvis_chunks,
        gpt_points=gpt_points,
        dry_run=args.dry_run,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
