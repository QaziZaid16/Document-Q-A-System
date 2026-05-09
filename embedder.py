from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)

def embed_chunks(chunks: List[str]) -> np.ndarray:
    """
    Takes a list of text strings and converts each one into a vector.

    chunks: list of strings (our PDF chunks)
    Returns: a 2D NumPy array of shape (num_chunks, 384)
             e.g. 50 chunks → array of shape (50, 384)
    """

    print(f"Embedding {len(chunks)} chunks...")

    embeddings = model.encode(
        chunks,      
    )

    print(f"Embedding complete. Shape: {embeddings.shape}")
    return embeddings

def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:

    embeddings = embeddings.astype('float32')
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"FAISS index built with {index.ntotal} vectors.")

    return index

def save_index(index: faiss.IndexFlatL2, chunks: List[str], path: str = "index_store"):

    os.makedirs(path, exist_ok=True)
    faiss.write_index(index, f"{path}/faiss.index")
    with open(f"{path}/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print(f"Saved index and {len(chunks)} chunks to '{path}/'")


def load_index(path: str = "index_store") -> Tuple[faiss.IndexFlatL2, List[str]]:

    index = faiss.read_index(f"{path}/faiss.index")
    with open(f"{path}/chunks.pkl", "rb") as f:
        chunks = pickle.load(f)

    print(f"Loaded index with {index.ntotal} vectors and {len(chunks)} chunks.")
    return index, chunks

def retrieve_relevant_chunks(
    query: str,
    index: faiss.IndexFlatL2,
    chunks: List[str],
    top_k: int = 3
) -> List[str]:
    """
    Given a user's question, finds the top_k most relevant chunks.
    This is the retrieval step of RAG.

    query:  the user's question as a plain string
    index:  the loaded FAISS index containing all chunk vectors
    chunks: the list of original chunk strings (matched by position to the index)
    top_k:  how many chunks to return (default 3)

    Returns: a list of the top_k most relevant chunk strings
    """

    query_vector = model.encode([query], convert_to_numpy=True)
    query_vector = query_vector.astype('float32')
    distances, indices = index.search(query_vector, top_k)
    relevant_chunks = [chunks[i] for i in indices[0]]

    return relevant_chunks

def build_or_load_index(chunks: List[str], index_path: str = "index_store"):
    """
    Smart helper: if an index already exists on disk, load it.
    If not, build it fresh from the chunks.

    This means: if the user uploads the same PDF again, we skip re-embedding.
    Re-embedding is the slowest step (~2-5 seconds), so this is a nice optimization.
    """

    if os.path.exists(f"{index_path}/faiss.index"):
        print("Found existing index. Loading from disk...")
        return load_index(index_path)
    else:
        print("No existing index. Building fresh...")
        embeddings = embed_chunks(chunks)
        index = build_faiss_index(embeddings)
        save_index(index, chunks, index_path)
        return index, chunks