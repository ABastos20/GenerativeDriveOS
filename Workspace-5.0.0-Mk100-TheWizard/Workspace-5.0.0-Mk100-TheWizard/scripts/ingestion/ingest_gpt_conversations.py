#!/usr/bin/env python3
"""Ingest GPT export conversations into JARVIS memory.

This script processes conversations.json from GPT export and ingests them
into Qdrant for semantic search.

Usage:
    python scripts/ingest_gpt_conversations.py
    python scripts/ingest_gpt_conversations.py --dry-run
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

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import structlog
from qdrant_client.http import models as qmodels

from jarvis.database.qdrant import get_qdrant_client, collection_exists, init_collection

logger = structlog.get_logger(__name__)


def load_conversations(export_path: Path) -> List[Dict[str, Any]]:
    """Load conversations from GPT export JSON."""
    logger.info("loading_conversations", path=str(export_path))

    with open(export_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conversations = data if isinstance(data, list) else [data]
    logger.info("conversations_loaded", count=len(conversations))

    return conversations


def extract_conversation_messages(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract messages from conversation structure."""
    messages = []

    # GPT export structure: conversation -> mapping -> node_id -> message
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
    """Chunk conversation into smaller pieces for embedding."""
    messages = extract_conversation_messages(conversation)

    title = conversation.get('title', 'Untitled Conversation')
    create_time = conversation.get('create_time', time.time())
    conv_id = conversation.get('id', str(uuid4()))

    chunks = []
    current_chunk = []
    current_size = 0

    for msg in messages:
        msg_text = f"{msg['role']}: {msg['text']}\n\n"
        msg_size = len(msg_text)

        if current_size + msg_size > max_chunk_size and current_chunk:
            # Save current chunk
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

    # Save last chunk
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


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using sentence-transformers."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def ingest_conversation(conversation: Dict[str, Any], client: Any, collection_name: str, dry_run: bool = False) -> int:
    """Ingest a single conversation into Qdrant."""
    chunks = chunk_conversation(conversation)

    if not chunks:
        logger.warning("no_chunks_extracted", conversation_id=conversation.get('id'))
        return 0

    if dry_run:
        logger.info("dry_run_chunks", count=len(chunks), title=conversation.get('title'))
        return len(chunks)

    points = []

    for chunk in chunks:
        try:
            # Generate embedding
            embedding = generate_embedding(chunk['text'])

            # Create point
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

        except Exception as e:
            logger.error("embedding_failed", chunk_index=chunk['chunk_index'], error=str(e))
            continue

    if points:
        try:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info("conversation_ingested", title=conversation.get('title'), chunks=len(points))
        except Exception as e:
            logger.error("upsert_failed", title=conversation.get('title'), error=str(e))
            return 0

    return len(points)


def main() -> int:
    """Main ingestion workflow."""
    parser = argparse.ArgumentParser(
        description="Ingest GPT export conversations into JARVIS memory"
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=Path("docs/gpt export/conversations.json"),
        help="Path to conversations.json from GPT export"
    )
    parser.add_argument(
        "--collection",
        default="knowledge",
        help="Qdrant collection name (default: knowledge)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - don't actually ingest"
    )

    args = parser.parse_args()

    try:
        # Ensure export file exists
        if not args.export_path.exists():
            logger.error("export_file_not_found", path=str(args.export_path))
            return 1

        # Load conversations
        conversations = load_conversations(args.export_path)

        if not args.dry_run:
            # Get Qdrant client and ensure collection exists
            client = get_qdrant_client()

            if not collection_exists(args.collection, client=client):
                logger.info("initializing_collection", collection=args.collection)
                init_collection(collection_name=args.collection, client=client)
        else:
            client = None

        # Ingest each conversation
        total_chunks = 0
        for i, conv in enumerate(conversations):
            logger.info("processing_conversation", index=i+1, total=len(conversations), title=conv.get('title'))
            chunks_count = ingest_conversation(conv, client, args.collection, dry_run=args.dry_run)
            total_chunks += chunks_count

        logger.info("ingestion_complete", conversations=len(conversations), total_chunks=total_chunks, dry_run=args.dry_run)
        return 0

    except Exception as e:
        logger.error("ingestion_failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
