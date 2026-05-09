"""
Core module containing RAG pipeline components.

Exports:
  - pdf_processor: PDF extraction and chunking
  - embedder: Vector embeddings and retrieval
  - llm_handler: LLM querying and answers
"""

from .pdf_processor import process_pdf
from .embedder import build_or_load_index, retrieve_relevant_chunks
from .llm_handler import get_answer, check_ollama_status

__all__ = [
    "process_pdf",
    "build_or_load_index",
    "retrieve_relevant_chunks",
    "get_answer",
    "check_ollama_status",
]
