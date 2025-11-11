"""
Generate embeddings for extracted text and save as CSV
Uses sentence-transformers for high-quality embeddings
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences for embedding.
    Uses simple regex-based sentence splitting.
    """
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split on sentence boundaries (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Filter out empty sentences and very short ones
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    return sentences


def split_into_chunks(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks by word count.
    Useful for longer documents.
    
    Args:
        text: Input text to split
        chunk_size: Target number of words per chunk
        overlap: Number of overlapping words between chunks
    """
    words = text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += (chunk_size - overlap)
    
    return chunks


def generate_embeddings(
    text: str,
    model_name: str = 'all-MiniLM-L6-v2',
    split_method: str = 'chunks',
    chunk_size: int = 400,
    overlap: int = 50
) -> Tuple[List[str], np.ndarray]:
    """
    Generate embeddings for text.
    
    Args:
        text: Input text to embed
        model_name: Sentence transformer model name
        split_method: 'sentences' or 'chunks'
        chunk_size: For chunk method, words per chunk
        overlap: For chunk method, overlapping words
    
    Returns:
        Tuple of (text_segments, embeddings_array)
    """
    if not HAS_SENTENCE_TRANSFORMERS:
        raise RuntimeError(
            "sentence-transformers not installed. Install with:\n"
            "pip install sentence-transformers"
        )
    
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Split text based on method
    if split_method == 'sentences':
        logger.info("Splitting text into sentences...")
        text_segments = split_into_sentences(text)
    elif split_method == 'chunks':
        logger.info(f"Splitting text into chunks (size={chunk_size}, overlap={overlap})...")
        text_segments = split_into_chunks(text, chunk_size, overlap)
    else:
        raise ValueError(f"Unknown split_method: {split_method}")
    
    logger.info(f"Generated {len(text_segments)} text segments")
    
    # Generate embeddings
    logger.info("Generating embeddings...")
    embeddings = model.encode(text_segments, show_progress_bar=True)
    
    logger.info(f"Embeddings shape: {embeddings.shape}")
    
    return text_segments, embeddings


def save_embeddings_csv(
    text_segments: List[str],
    embeddings: np.ndarray,
    output_path: Path
) -> None:
    """
    Save text segments and embeddings to CSV.
    
    CSV format:
    - Column 1: 'text' - the text segment
    - Column 2: 'embedding' - the embedding vector as string (list format)
    """
    # Convert embeddings to list format for CSV storage
    embedding_lists = [emb.tolist() for emb in embeddings]
    
    # Create dataframe
    df = pd.DataFrame({
        'text': text_segments,
        'embedding': embedding_lists
    })
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved embeddings to: {output_path}")
    logger.info(f"CSV contains {len(df)} rows")
    logger.info(f"Embedding dimension: {len(embedding_lists[0])}")


def process_extracted_text(
    text_file_path: str,
    output_csv_path: str = None,
    model_name: str = 'all-MiniLM-L6-v2',
    split_method: str = 'chunks',
    chunk_size: int = 400,
    overlap: int = 50
) -> str:
    """
    Complete pipeline: read extracted text, generate embeddings, save CSV.
    
    Args:
        text_file_path: Path to extracted text file
        output_csv_path: Path for output CSV (auto-generated if None)
        model_name: Sentence transformer model
        split_method: 'sentences' or 'chunks'
        chunk_size: Words per chunk (if chunks method)
        overlap: Overlapping words (if chunks method)
    
    Returns:
        Path to output CSV file
    """
    text_path = Path(text_file_path)
    
    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {text_file_path}")
    
    # Read text
    logger.info(f"Reading text from: {text_path}")
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    word_count = len(text.split())
    logger.info(f"Loaded {word_count} words")
    
    # Generate embeddings
    text_segments, embeddings = generate_embeddings(
        text,
        model_name=model_name,
        split_method=split_method,
        chunk_size=chunk_size,
        overlap=overlap
    )
    
    # Determine output path
    if output_csv_path is None:
        output_csv_path = text_path.parent.parent / "embeddings" / (text_path.stem + "_embeddings.csv")
    
    output_csv_path = Path(output_csv_path)
    
    # Save to CSV
    save_embeddings_csv(text_segments, embeddings, output_csv_path)
    
    return str(output_csv_path)


def main():
    """
    Main entry point for CLI usage
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings from extracted text")
    parser.add_argument('input_file', help='Path to extracted text file')
    parser.add_argument('--output', '-o', help='Output CSV path (auto-generated if not provided)')
    parser.add_argument('--model', default='all-MiniLM-L6-v2', 
                       help='Sentence transformer model name (default: all-MiniLM-L6-v2)')
    parser.add_argument('--split', choices=['sentences', 'chunks'], default='chunks',
                       help='Text splitting method (default: sentences)')
    parser.add_argument('--chunk-size', type=int, default=400,
                       help='Words per chunk for chunks method (default: 200)')
    parser.add_argument('--overlap', type=int, default=50,
                       help='Overlapping words for chunks method (default: 50)')
    
    args = parser.parse_args()
    
    try:
        output_path = process_extracted_text(
            args.input_file,
            args.output,
            args.model,
            args.split,
            args.chunk_size,
            args.overlap
        )
        
        print("\n" + "="*70)
        print("EMBEDDING GENERATION COMPLETE!")
        print("="*70)
        print(f"Input:  {args.input_file}")
        print(f"Output: {output_path}")
        print("="*70)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
