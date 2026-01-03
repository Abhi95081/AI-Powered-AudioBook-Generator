"""
Utilities to generate text embeddings and save them to CSV for downstream vector DB usage.
Uses a local SentenceTransformer model (all-MiniLM-L6-v2) by default.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from sentence_transformers import SentenceTransformer


def _split_text_into_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into word-based chunks with overlap to preserve context."""
    words = text.split()
    if not words:
        return []

    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks: List[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        end = start + chunk_size
        chunk_words = words[start:end]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
    return chunks


def generate_embeddings(
    text: str,
    model_name: str = "all-MiniLM-L6-v2",
    split_method: str = "chunks",
    chunk_size: int = 400,
    overlap: int = 50,
) -> Optional[Tuple[List[str], List[List[float]]]]:
    """
    Generate embeddings for the given text.

    Returns a tuple (text_segments, embeddings_array) or None on failure.
    """
    if not text or not text.strip():
        return None

    segments = _split_text_into_chunks(text, chunk_size=chunk_size, overlap=overlap)
    if not segments:
        return None

    # Load local embedding model
    model = SentenceTransformer(f"sentence-transformers/{model_name}")
    embeddings = model.encode(segments, normalize_embeddings=True, show_progress_bar=False)

    # Convert numpy array to plain lists for serialization
    embeddings_list: List[List[float]] = [emb.tolist() for emb in embeddings]
    return segments, embeddings_list


def save_embeddings_csv(text_segments: List[str], embeddings_array: List[List[float]], csv_path: Path) -> Path:
    """Save embeddings and text segments to CSV with columns: text, embedding."""
    df = pd.DataFrame({
        "text": text_segments,
        "embedding": [emb for emb in embeddings_array],
    })
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return csv_path
