"""
embedder.py
===========
Purpose: Convert text chunks into vector embeddings and manage FAISS indices.
This is the middle layer of the RAG pipeline.

Pipeline:
  1. embed_chunks: Text chunks → vectors (using SentenceTransformer)
  2. build_faiss_index: Vectors → searchable FAISS index
  3. retrieve_relevant_chunks: Query → find K nearest chunks
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================
print("[Embedder] Loading configuration...")
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, CPU-friendly embedding model
print(f"[Embedder] Model name: {MODEL_NAME}")

# === LOAD EMBEDDING MODEL ===
print("[Embedder] Loading SentenceTransformer model (this may take 30s on first run)...")
try:
    model = SentenceTransformer(MODEL_NAME)
    print(f"[Embedder] ✓ Model loaded successfully")
except Exception as e:
    print(f"[Embedder] ❌ Failed to load model: {e}")
    raise

# ============================================================================
# EMBEDDING FUNCTION
# ============================================================================

def embed_chunks(chunks: List[str]) -> np.ndarray:
    """
    STEP 1: Convert text chunks into vector embeddings.
    
    Purpose: Uses SentenceTransformer to convert each text chunk into a 
             384-dimensional vector that captures semantic meaning.
             These vectors are then used for similarity search.
    
    Args:
        chunks (List[str]): List of text strings to embed
        
    Returns:
        np.ndarray: 2D array of shape (num_chunks, 384)
                   Each row is a 384-dim embedding vector
                   
    Raises:
        ValueError: If chunks list is empty
        TypeError: If chunks is not a list of strings
    """
    # === INPUT VALIDATION ===
    if not isinstance(chunks, list):
        raise TypeError(f"Expected list of chunks, got {type(chunks)}")
    
    if len(chunks) == 0:
        raise ValueError("Cannot embed empty chunks list")
    
    if not all(isinstance(c, str) for c in chunks):
        raise TypeError("All chunks must be strings")
    
    print(f"[Embedder] ⏳ Embedding {len(chunks)} chunks using {MODEL_NAME}...")
    
    try:
        # === ENCODE CHUNKS INTO VECTORS ===
        embeddings = model.encode(
            chunks,
            convert_to_numpy=True,  # Return numpy array instead of torch tensor
            show_progress_bar=True  # Show progress bar during encoding
        )
        
        # === VALIDATION ===
        print(f"[Embedder] ✓ Embedding complete")
        print(f"[Embedder] Shape: {embeddings.shape} (rows=chunks, cols=dimensions)")
        print(f"[Embedder] Data type: {embeddings.dtype}")
        print(f"[Embedder] Vector range: [{embeddings.min():.4f}, {embeddings.max():.4f}]")
        
        return embeddings
        
    except Exception as e:
        print(f"[Embedder] ❌ Error during embedding: {e}")
        raise


# ============================================================================
# FAISS INDEX BUILDING
# ============================================================================

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """
    STEP 2: Build searchable FAISS index from embeddings.
    
    Purpose: Creates an index that enables fast similarity search using L2 distance.
             FAISS can search 1M+ vectors in milliseconds.
    
    Args:
        embeddings (np.ndarray): 2D array of shape (num_chunks, 384)
        
    Returns:
        faiss.IndexFlatL2: Trained index ready for searches
        
    Raises:
        ValueError: If embeddings is empty or wrong shape
        TypeError: If embeddings is not numpy array
    """
    # === INPUT VALIDATION ===
    if not isinstance(embeddings, np.ndarray):
        raise TypeError(f"Expected numpy array, got {type(embeddings)}")
    
    if embeddings.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape {embeddings.shape}")
    
    if embeddings.shape[0] == 0:
        raise ValueError("Cannot build index from empty embeddings")
    
    print(f"[Embedder] Building FAISS index...")
    
    try:
        # === CONVERT TO FLOAT32 (required by FAISS) ===
        embeddings = embeddings.astype('float32')
        print(f"[Embedder] Converted to float32")
        
        # === CREATE INDEX ===
        dimension = embeddings.shape[1]  # Should be 384 for this model
        index = faiss.IndexFlatL2(dimension)
        print(f"[Embedder] Created IndexFlatL2 with dimension={dimension}")
        
        # === ADD VECTORS TO INDEX ===
        index.add(embeddings)
        print(f"[Embedder] ✓ Added {index.ntotal} vectors to index")
        
        return index
        
    except Exception as e:
        print(f"[Embedder] ❌ Error building index: {e}")
        raise


# ============================================================================
# PERSISTENCE: Save/Load Index
# ============================================================================

def save_index(index: faiss.IndexFlatL2, chunks: List[str], path: str = "index_store"):
    """
    SAVE: Persist index and chunks to disk.
    
    Purpose: Save embeddings and chunks so we don't need to re-embed
             on subsequent app runs. Re-embedding is the slowest step.
    
    Args:
        index (faiss.IndexFlatL2): FAISS index to save
        chunks (List[str]): Original text chunks (for displaying to user)
        path (str): Directory path to save to
        
    Raises:
        Exception: If directory creation or file writing fails
    """
    print(f"[Embedder] Saving index and chunks...")
    
    try:
        # === CREATE DIRECTORY IF NEEDED ===
        os.makedirs(path, exist_ok=True)
        print(f"[Embedder] Directory ensured: {path}")
        
        # === SAVE FAISS INDEX ===
        index_path = f"{path}/faiss.index"
        faiss.write_index(index, index_path)
        print(f"[Embedder] ✓ Index saved: {index_path}")
        
        # === SAVE CHUNKS AS PICKLE ===
        chunks_path = f"{path}/chunks.pkl"
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)
        print(f"[Embedder] ✓ Chunks saved: {chunks_path}")
        
        print(f"[Embedder] ✓ Saved {len(chunks)} chunks and index to '{path}/'")
        
    except Exception as e:
        print(f"[Embedder] ❌ Error saving index: {e}")
        raise


def load_index(path: str = "index_store") -> Tuple[faiss.IndexFlatL2, List[str]]:
    """
    LOAD: Restore index and chunks from disk.
    
    Purpose: Load previously saved index to skip re-embedding step.
    
    Args:
        path (str): Directory path to load from
        
    Returns:
        Tuple[faiss.IndexFlatL2, List[str]]: (index, chunks)
        
    Raises:
        FileNotFoundError: If index or chunks file doesn't exist
    """
    print(f"[Embedder] Loading index and chunks from '{path}'...")
    
    try:
        # === LOAD FAISS INDEX ===
        index_path = f"{path}/faiss.index"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index not found: {index_path}")
        
        index = faiss.read_index(index_path)
        print(f"[Embedder] ✓ Index loaded ({index.ntotal} vectors)")
        
        # === LOAD CHUNKS ===
        chunks_path = f"{path}/chunks.pkl"
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks not found: {chunks_path}")
        
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        print(f"[Embedder] ✓ Chunks loaded ({len(chunks)} chunks)")
        
        return index, chunks
        
    except Exception as e:
        print(f"[Embedder] ❌ Error loading index: {e}")
        raise


# ============================================================================
# RETRIEVAL: Find Relevant Chunks
# ============================================================================

def retrieve_relevant_chunks(
    query: str,
    index: faiss.IndexFlatL2,
    chunks: List[str],
    top_k: int = 3
) -> List[str]:
    """
    RETRIEVAL: Find K most relevant chunks for a user query.
    
    Purpose: This is the core of RAG retrieval. Given a user question,
             find the most semantically similar document chunks.
    
    Process:
      1. Embed the query using same model as chunks
      2. Search FAISS index for nearest neighbors
      3. Return original chunk text (not vectors)
    
    Args:
        query (str): User's question
        index (faiss.IndexFlatL2): FAISS index
        chunks (List[str]): Original chunk texts (parallel to index)
        top_k (int): Number of chunks to retrieve (default: 3)
        
    Returns:
        List[str]: Top K most relevant chunks in order
        
    Raises:
        ValueError: If top_k invalid or query empty
        TypeError: If types are wrong
    """
    # === INPUT VALIDATION ===
    if not isinstance(query, str) or len(query.strip()) == 0:
        raise ValueError("Query must be non-empty string")
    
    if top_k <= 0 or top_k > len(chunks):
        raise ValueError(f"top_k must be in range [1, {len(chunks)}], got {top_k}")
    
    if len(chunks) == 0:
        raise ValueError("Cannot retrieve from empty chunks list")
    
    print(f"[Embedder] 🔍 Retrieving top {top_k} chunks for query: '{query[:50]}...'")
    
    try:
        # === EMBED QUERY ===
        query_vector = model.encode([query], convert_to_numpy=True)
        query_vector = query_vector.astype('float32')
        print(f"[Embedder] Query embedded to shape {query_vector.shape}")
        
        # === SEARCH INDEX ===
        distances, indices = index.search(query_vector, top_k)
        print(f"[Embedder] Search complete. Retrieved indices: {indices[0]}")
        
        # === RETRIEVE ORIGINAL CHUNKS ===
        relevant_chunks = [chunks[i] for i in indices[0]]
        
        # === DEBUG: Show similarity scores ===
        for rank, (idx, distance) in enumerate(zip(indices[0], distances[0]), 1):
            # FAISS uses L2 distance (lower = more similar)
            similarity = 1 / (1 + distance)  # Convert to 0-1 range
            print(f"[Embedder]   Rank {rank}: chunk#{idx} (similarity: {similarity:.3f})")
        
        print(f"[Embedder] ✓ Retrieved {len(relevant_chunks)} chunks")
        return relevant_chunks
        
    except Exception as e:
        print(f"[Embedder] ❌ Error retrieving chunks: {e}")
        raise


# ============================================================================
# SMART HELPER: Build or Load Index
# ============================================================================

def build_or_load_index(chunks: List[str], index_path: str = "index_store"):
    """
    SMART HELPER: Build index fresh OR load from disk if it exists.
    
    Purpose: Optimization layer. If we've already embedded these chunks,
             skip the expensive embedding step and load from disk instead.
             
    Flow:
      - If index exists on disk → load it (fast, ~100ms)
      - If not → build fresh (slow, ~2-5s for 1000 chunks)
    
    Args:
        chunks (List[str]): Text chunks to index
        index_path (str): Directory for storing/loading index
        
    Returns:
        Tuple[faiss.IndexFlatL2, List[str]]: (index, chunks)
    """
    print(f"[Embedder] Checking for existing index at '{index_path}'...")
    
    try:
        if os.path.exists(f"{index_path}/faiss.index"):
            print(f"[Embedder] Found existing index. Loading from disk...")
            return load_index(index_path)
        else:
            print(f"[Embedder] No existing index. Building fresh...")
            embeddings = embed_chunks(chunks)
            index = build_faiss_index(embeddings)
            save_index(index, chunks, index_path)
            print(f"[Embedder] ✓ Fresh index built and saved")
            return index, chunks
            
    except Exception as e:
        print(f"[Embedder] ❌ Error in build_or_load_index: {e}")
        raise
