"""
Save embeddings to a vector database (ChromaDB)
Allows for efficient similarity search and retrieval
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import List, Dict, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("chromadb not installed. Install with: pip install chromadb")


def load_embeddings_from_csv(csv_path: str) -> tuple[List[str], List[List[float]], List[Dict]]:
    """
    Load embeddings from CSV file.
    
    Args:
        csv_path: Path to embeddings CSV file
        
    Returns:
        Tuple of (texts, embeddings, metadata)
    """
    logger.info(f"Loading embeddings from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    texts = df['text'].tolist()
    
    # Convert embedding strings to lists
    embeddings = []
    for emb_str in df['embedding']:
        emb_list = json.loads(emb_str.replace("'", '"'))
        embeddings.append(emb_list)
    
    # Create metadata for each text segment
    metadata = []
    for idx, text in enumerate(texts):
        metadata.append({
            'index': idx,
            'source': Path(csv_path).stem,
            'length': len(text)
        })
    
    logger.info(f"Loaded {len(texts)} text segments with {len(embeddings[0])}-dimensional embeddings")
    return texts, embeddings, metadata


def create_vectordb(
    collection_name: str = "audiobook_embeddings",
    persist_directory: str = "./vectordb"
) -> chromadb.Collection:
    """
    Create or get a ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
        persist_directory: Directory to persist the database
        
    Returns:
        ChromaDB collection
    """
    if not HAS_CHROMADB:
        raise RuntimeError(
            "chromadb not installed. Install with:\n"
            "pip install chromadb"
        )
    
    # Create persistent client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Get or create collection
    try:
        collection = client.get_collection(name=collection_name)
        logger.info(f"Retrieved existing collection: {collection_name}")
    except:
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Audiobook text embeddings"}
        )
        logger.info(f"Created new collection: {collection_name}")
    
    return collection


def save_to_vectordb(
    csv_path: str,
    collection_name: str = "audiobook_embeddings",
    persist_directory: str = "./vectordb",
    batch_size: int = 100,
    clear_collection: bool = True
) -> str:
    """
    Save embeddings from CSV to vector database.
    
    Args:
        csv_path: Path to embeddings CSV file
        collection_name: Name of the vector DB collection
        persist_directory: Directory to persist the database
        batch_size: Number of embeddings to add per batch
        clear_collection: If True, clears existing collection before adding new documents
        
    Returns:
        Path to vector database directory
    """
    # Load embeddings
    texts, embeddings, metadata = load_embeddings_from_csv(csv_path)
    
    # Create persistent client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Clear and recreate collection if requested
    if clear_collection:
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Cleared existing collection: {collection_name}")
        except:
            pass
    
    # Create vector DB collection
    collection = create_vectordb(collection_name, persist_directory)
    
    # Generate unique IDs for each embedding based on source file
    source_name = Path(csv_path).stem
    ids = [f"{source_name}_{i}" for i in range(len(texts))]
    
    # Add to collection in batches
    logger.info(f"Adding {len(texts)} documents to collection in batches of {batch_size}...")
    
    for i in range(0, len(texts), batch_size):
        end_idx = min(i + batch_size, len(texts))
        batch_ids = ids[i:end_idx]
        batch_texts = texts[i:end_idx]
        batch_embeddings = embeddings[i:end_idx]
        batch_metadata = metadata[i:end_idx]
        
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=batch_embeddings,
            metadatas=batch_metadata
        )
        
        logger.info(f"Added batch {i//batch_size + 1}: documents {i} to {end_idx}")
    
    # Get collection info
    count = collection.count()
    logger.info(f"Vector database saved: {count} documents in collection '{collection_name}'")
    logger.info(f"Database location: {Path(persist_directory).absolute()}")
    
    return str(Path(persist_directory).absolute())


def query_vectordb(
    query_text: str,
    collection_name: str = "audiobook_embeddings",
    persist_directory: str = "./vectordb",
    n_results: int = 5,
    embedding_function = None
) -> Dict:
    """
    Query the vector database for similar texts.
    
    Args:
        query_text: Text to search for
        collection_name: Name of the collection
        persist_directory: Directory where DB is persisted
        n_results: Number of results to return
        embedding_function: Optional function to embed query (if None, uses ChromaDB default)
        
    Returns:
        Dictionary with query results
    """
    if not HAS_CHROMADB:
        raise RuntimeError("chromadb not installed")
    
    # Connect to database
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_collection(name=collection_name)
    
    # Query with text (ChromaDB will handle embedding if using default)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    return results


def list_collections(persist_directory: str = "./vectordb") -> List[str]:
    """
    List all collections in the vector database.
    
    Args:
        persist_directory: Directory where DB is persisted
        
    Returns:
        List of collection names
    """
    if not HAS_CHROMADB:
        raise RuntimeError("chromadb not installed")
    
    client = chromadb.PersistentClient(path=persist_directory)
    collections = client.list_collections()
    
    return [col.name for col in collections]


def get_collection_stats(
    collection_name: str = "audiobook_embeddings",
    persist_directory: str = "./vectordb"
) -> Dict:
    """
    Get statistics about a collection.
    
    Args:
        collection_name: Name of the collection
        persist_directory: Directory where DB is persisted
        
    Returns:
        Dictionary with collection statistics
    """
    if not HAS_CHROMADB:
        raise RuntimeError("chromadb not installed")
    
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_collection(name=collection_name)
    
    stats = {
        'name': collection.name,
        'count': collection.count(),
        'metadata': collection.metadata
    }
    
    return stats


def main():
    """
    Main entry point for CLI usage
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Save embeddings to vector database")
    parser.add_argument('csv_file', help='Path to embeddings CSV file')
    parser.add_argument('--collection', default='audiobook_embeddings',
                       help='Collection name (default: audiobook_embeddings)')
    parser.add_argument('--db-dir', default='./vectordb',
                       help='Vector database directory (default: ./vectordb)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for adding documents (default: 100)')
    parser.add_argument('--query', help='Query text for similarity search (optional)')
    parser.add_argument('--top-k', type=int, default=5,
                       help='Number of results for query (default: 5)')
    parser.add_argument('--list', action='store_true',
                       help='List all collections and exit')
    parser.add_argument('--stats', action='store_true',
                       help='Show collection statistics')
    
    args = parser.parse_args()
    
    try:
        # List collections
        if args.list:
            collections = list_collections(args.db_dir)
            print("\nAvailable collections:")
            for col in collections:
                print(f"  - {col}")
            return
        
        # Show stats
        if args.stats:
            stats = get_collection_stats(args.collection, args.db_dir)
            print("\nCollection Statistics:")
            print(f"  Name: {stats['name']}")
            print(f"  Documents: {stats['count']}")
            print(f"  Metadata: {stats['metadata']}")
            return
        
        # Save embeddings to vector DB
        db_path = save_to_vectordb(
            args.csv_file,
            args.collection,
            args.db_dir,
            args.batch_size
        )
        
        print("\n" + "="*70)
        print("VECTOR DATABASE SAVED!")
        print("="*70)
        print(f"CSV Input:    {args.csv_file}")
        print(f"Collection:   {args.collection}")
        print(f"DB Location:  {db_path}")
        print("="*70)
        
        # Optional query
        if args.query:
            print(f"\nQuerying: '{args.query}'")
            print(f"Top {args.top_k} results:")
            print("-" * 70)
            
            results = query_vectordb(
                args.query,
                args.collection,
                args.db_dir,
                args.top_k
            )
            
            for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0]), 1):
                print(f"\n{i}. (distance: {distance:.4f})")
                print(f"   {doc[:200]}{'...' if len(doc) > 200 else ''}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
